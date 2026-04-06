import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  loginLoginAccessToken,
  usersReadUserMe,
  usersRegisterUser,
  type Body_login_login_access_token as AccessToken,
  type UserPublic,
  type UserRegister,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const response = await usersReadUserMe() as { error?: any; response?: { status: number }; data: any }
      // Check for error in response
      if (response.error) {
        // Check HTTP status from response object
        const status = response.response?.status
        const errDetail = response.error?.detail

        // Handle authentication errors (401, 403)
        if (status === 401 || status === 403 ||
            errDetail === "Could not validate credentials" ||
            errDetail?.includes("not authenticated") ||
            errDetail?.includes("Not authenticated")) {
          // Clear the invalid token immediately
          localStorage.removeItem("access_token")
          queryClient.setQueryData(["currentUser"], null)
          // Redirect to login if not already there
          if (window.location.pathname !== "/login") {
            navigate({ to: "/login" })
          }
          return null
        }
        throw response.error
      }
      return response.data
    },
    enabled: isLoggedIn(),
    retry: false,
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      usersRegisterUser({ body: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await loginLoginAccessToken({ body: data })
    if (response.error) {
      throw response.error
    }
    localStorage.setItem("access_token", response.data.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: async () => {
      // Invalidate and refetch user data immediately after login
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
