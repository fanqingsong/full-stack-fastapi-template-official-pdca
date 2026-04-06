// Example test file
describe("Example Test", () => {
  it("should load the homepage", () => {
    cy.visit("/")
    cy.contains("Full Stack FastAPI Project").should("exist")
  })
})
