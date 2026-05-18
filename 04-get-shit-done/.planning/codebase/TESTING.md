---
title: Testing
last_mapped: 2026-05-18
---

# Testing

## Framework

- **E2E**: Playwright (`e2e/`) — primary test layer
- **Backend unit tests**: None found in current codebase (no `tests/` directory)
- **Frontend unit tests**: None found in current codebase

## Structure

```
e2e/
├── playwright.config.ts     # Config: headless, 1 retry in CI, base URL http://localhost:5173
├── pages/
│   ├── base.page.ts         # BasePage — shared locators and helpers
│   ├── home.page.ts         # HomePage — extends BasePage
│   └── prompt-list.page.ts  # PromptListPage — extends BasePage
└── tests/
    ├── home.spec.ts          # Home page tests
    └── prompt-list.spec.ts   # Prompt list CRUD tests
```

## Page Object Model

All pages extend `BasePage` and store locators as class properties:
```typescript
export class PromptListPage extends BasePage {
  readonly createButton: Locator
  readonly nameInput: Locator

  constructor(page: Page) {
    super(page)
    this.createButton = page.getByRole('button', { name: '创建' })
    this.nameInput = page.getByPlaceholder('请输入名称')
  }
}
```

BasePage provides shared helpers:
- `screenshot(name)` — capture named screenshot
- `getCellText(row, col)` — get table cell text
- `waitForNetworkIdle()` — wait for requests to complete

## Test Structure

```typescript
test.describe('Prompt List', () => {
  let page: PromptListPage

  test.beforeEach(async ({ page: p }) => {
    page = new PromptListPage(p)
    await page.goto('/prompts')
  })

  test('should display prompt list', async () => {
    await expect(page.table).toBeVisible()
  })
})
```

## Configuration

`e2e/playwright.config.ts`:
- **baseURL**: `http://localhost:5173`
- **headless**: true by default
- **retries**: 1 in CI, 0 locally
- **reporter**: list

## Mocking

No API mocking — tests run against real backend (requires both servers running).

## Coverage

- E2E covers home page stats and prompt list CRUD
- **Agent functionality**: not yet tested (to be added)
- No backend unit test coverage

## Running Tests

```bash
# Install dependencies
cd e2e && npm install

# Run all E2E tests (requires backend + frontend running)
cd e2e && npx playwright test

# Run specific file
cd e2e && npx playwright test tests/prompt-list.spec.ts

# Run with UI
cd e2e && npx playwright test --ui
```
