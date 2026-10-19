# Screenshots

Captured from the running system: the API started with `start_api.bat`, the
browser UI in a headless browser, the desktop app driven against the same API,
and the test suite run with `run_tests.bat`. The training and evaluation
figures themselves are in `outputs/figures/` and inside the notebook.

| File | What it shows |
|---|---|
| `01-web-phishing-verdict.png` | Browser UI: the phishing example flagged at over 99.9%, the probability bar against the 0.54 threshold, and the LIME words underlined in the email with their weights |
| `02-web-legitimate-verdict.png` | Browser UI: an ordinary meeting email passed as legitimate, with its explanation |
| `03-web-empty-input-message.png` | Browser UI: the message shown when Analyse is clicked with no text |
| `04-web-model-results.png` | Model page: test results for the CNN and the logistic regression baseline, the loss curve with early stopping, the confusion matrix, ROC and precision-recall curves |
| `05-web-about-page.png` | About page with every technical section open: data, model, threshold, LIME, API, security, desktop app and tests |
| `06-web-phone-width.png` | The browser UI at phone width |
| `07-api-interactive-docs.png` | The interactive API documentation at `/docs` |
| `08-desktop-phishing-verdict.png` | Desktop app: the phishing example flagged as Critical risk |
| `09-desktop-lime-explanation.png` | Desktop app: the LIME explanation window for that email |
| `10-desktop-legitimate-verdict.png` | Desktop app: the meeting email passed as legitimate |
| `11-tests-passing.png` | The test suite: 18 tests on the endpoints, validation, threshold logic and security layer, all passing |
