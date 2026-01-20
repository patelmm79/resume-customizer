git add -A
$commitMessage = 'fix(terraform): run Cloud Build in-cloud via google_cloudbuild_build; grant Cloud Build repo writer; update docs'
if (-not (git diff --cached --quiet)) {
  git commit -m "$commitMessage"
} else {
  Write-Output "no changes to commit"
}

git push
