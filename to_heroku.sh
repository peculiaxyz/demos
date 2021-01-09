COMMIT_MSG=$1

git init
git add .
git commit -m "$COMMIT_MSG"

git push heroku master