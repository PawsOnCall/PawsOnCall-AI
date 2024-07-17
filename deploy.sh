docker rm -f assistants-api 2>/dev/null || true
docker build -t assistants-api .
docker run -p 3000:3000 -d --name assistants-api assistants-api
