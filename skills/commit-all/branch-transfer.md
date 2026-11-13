# Branch transfer (step 2, options 2 and 3)

Used when the current branch carries another session's commits and the user chose a new
branch. The transfer happens in a separate worktree next to the clone, never by
`git checkout -- <paths>` in the shared checkout: a failure at any step then erases
nothing, and the session's files stay in place in the original checkout.

1. Save the session's patch outside the repository first (`git diff --binary HEAD --
   <session paths>` into a file under a scratch directory) and keep it until the new
   commit is verified.
2. For option 2, check the patch against the target without touching the checkout, in a
   temporary index: `GIT_INDEX_FILE=<tmp> git read-tree origin/<default>`, then
   `git diff --binary HEAD -- <paths> | GIT_INDEX_FILE=<tmp> git apply --cached --check -`
   (pass the raw stdout). A failure such as `does not exist in index` means a session
   file exists only on the other branch: option 2 is unavailable, offer option 3.
3. Create the worktree in a separate call from the base (`origin/<default>` for option 2,
   the current `HEAD` for option 3), with a branch named by the step 2 convention:
   `git worktree add -b <branch> <clone>-<topic> <base>`. Option 3 names the dependency on
   the other branch's pull request and the merge order.
4. Copy only the session's files into the worktree (for a file with foreign hunks, build
   the session's version with `git show HEAD:<path>` plus the session's edits, as in
   Mechanics), stage them there, run the snapshot check, and commit there.
5. Verify `git -C <clone>-<topic> show --stat --format= HEAD` lists every session file.
   An empty commit or a short list is a stop: change nothing in the original working
   tree and report.
6. Report the new branch, the worktree path and that the original checkout still holds
   the same changes uncommitted; removing them or the worktree is the user's decision.
