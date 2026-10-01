# Thread links through Google

Google is open in the Claude in Chrome extension; only reddit.com is refused. Stay on the Google
results page: its text sits on google.com.

For each query open `https://www.google.com/search?num=20&q=site:reddit.com+<query>` and run this in
the page:

```js
[...document.querySelectorAll('a[href*="reddit.com/r/"]')]
  .filter(a => a.querySelector('h3') && a.href.includes('/comments/'))
  .map(a => a.href.split('?')[0] + ' | ' + a.querySelector('h3').innerText).join('\n')
```

Each line is `<thread URL> | <title>`. Put the lines of all queries in one text file, then clean it:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/reddit_voc.py" links < raw-results.txt > urls.txt
```

Read the titles and delete the off-topic threads from `urls.txt`: each thread left in it costs money.

Done when `urls.txt` holds only thread URLs whose titles are on the topic.
