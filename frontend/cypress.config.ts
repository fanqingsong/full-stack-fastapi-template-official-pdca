import { defineConfig } from "cypress"
import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables from root .env file
dotenv.config({ path: path.join(__dirname, "../.env") })

export default defineConfig({
  e2e: {
    // Allow baseUrl to be overridden by environment variable for Docker
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:5173",
    setupNodeEvents(on, config) {
      // Load environment variables into Cypress config
      config.env.FIRST_SUPERUSER = process.env.FIRST_SUPERUSER
      config.env.FIRST_SUPERUSER_PASSWORD = process.env.FIRST_SUPERUSER_PASSWORD

      return config
    },
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
    supportFile: "cypress/support/e2e.ts",
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
  },
})
