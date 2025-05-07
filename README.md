## Twitter MCP Server
> This repo is used to run a twitter mcp server. It provides base oauth2.0 and send tweet. And also provide function to refresh token.
> For apis have limits, we handle http error 429, and refresh the limit state while refresh token. So you should set property interval
> for refresh, recommend 30min.

1. env
 copy `.env.example` to `.env` in the project direct
```commandline
SERVER_DOMAIN= # callback domain for X oauth2.0
X_CLIENT_ID= # X's client id
X_CLIENT_SECRET= # X's client secret
PORT= # current mcp server port
```

2. Start server
```commandline
python main.py
```

3. Test [test](test.py)