# Web Text Extraction Guidelines

Use this reference when a task involves policy-sensitive crawling decisions,
output cleanup choices, or reporting limitations from public webpages.

## Boundaries

- Extract text only from public `http` and `https` webpages or saved HTML files.
- Do not bypass logins, paywalls, robots.txt restrictions, rate limits, CAPTCHA, IP blocks, or anti-bot controls.
- Do not use credentials embedded in URLs.
- Stop and explain the limitation when a site blocks access or requires interactive verification.
- Prefer official APIs, feeds, exports, or downloadable files when the site provides them for the requested data.

## Polite Fetching

- Identify requests with a clear user agent.
- Check robots.txt before fetching a live URL.
- Use conservative timeouts.
- Add a delay between robots checks and page fetches; increase the delay when fetching multiple URLs.
- Fetch only the URLs needed for the user's task.
- Cache or save source outputs when repeated analysis is expected.

## Extraction Quality

- Preserve source records: original URL, final URL, fetch time, HTTP status, content type, and robots decision when available.
- Remove boilerplate that is clearly non-content, such as scripts, styles, hidden elements, navigation, and duplicated whitespace.
- Preserve headings, paragraph boundaries, list item separation, and table cell text when they are meaningful.
- Keep quoted webpage text brief in final answers. Summarize and cite sources when responding to the user.
- If extraction is partial, say so and name the likely cause.

## Failure Modes

- `robots.txt` disallows the URL: do not fetch; report that the site policy blocks the request.
- Robots policy cannot be fetched: fail closed for live crawling unless the user provides a saved HTML file.
- HTTP 401, 403, 407, 429, or CAPTCHA: do not retry aggressively or attempt workarounds.
- Non-HTML content: use a format-specific extractor only when the user asked for that content type and the relevant skill/tooling is available.
- JavaScript-rendered pages: use a browser only for public pages that allow automated access; do not use it to bypass restrictions.

## Suggested Output Shape

For saved artifacts, prefer Markdown or JSON with:

- Source metadata
- Page title
- Extracted text
- Character and word counts
- Notes about access restrictions or partial extraction
