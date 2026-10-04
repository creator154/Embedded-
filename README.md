# Live Test Wrapper

## Local
```bash
pip install -r requirements.txt
ADMIN_PASSWORD=yourpassword python app.py
```

Open `/admin`.

## Heroku/Render
Set environment variables:
- `SECRET_KEY` = random long value
- `ADMIN_PASSWORD` = your admin password

The app stores data in SQLite for a simple MVP. For production on Heroku/Render, use PostgreSQL because the local filesystem can be reset.

## Important result limitation
The wrapper can save results only when the embedded quiz sends a message like:
```js
window.parent.postMessage({
  type: "QUIZ_RESULT",
  score: 178,
  correct: 178,
  wrong: 2
}, "https://YOUR-WRAPPER-DOMAIN");
```
A cross-origin iframe cannot be inspected by the wrapper with JavaScript. If Quizard does not provide an API or `postMessage` result, the wrapper can display the test but cannot automatically read the student's score.
