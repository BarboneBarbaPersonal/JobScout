# JobScout - your personal job board

JobScout checks the careers pages of the companies **you** choose every hour, keeps only the
jobs that fit **your** preferences, and shows them on your own web page.
It's free, and you don't need to write any code.

## Get your own (about 15 minutes)

**Follow the step-by-step guide:
[barbonebarbapersonal.github.io/JobScout/setup.html](https://barbonebarbapersonal.github.io/JobScout/setup.html)**

In short:
1. Copy the [template Google Sheet](https://docs.google.com/spreadsheets/d/13m_zl9jKkAHnLnwL4PRx2R84i5jqD4YlsbCJo3EkAJA/copy),
   fill in **Preferences** (roles, languages, locations) and **Companies**, then share it as
   "Anyone with the link: Viewer".
2. Click **Use this template** (top of this page) to create your own copy of this project (Public).
3. In your copy, go to **Settings > Secrets and variables > Actions > New repository secret**:
   name `SHEET_URL`, value = your sheet link.
4. **Actions > Scan > Run workflow**, then **Settings > Pages**: deploy from branch `gh-pages`.
5. Your page: `https://<your-username>.github.io/<repo-name>/`

## Privacy - who can see what

| What | Who can see it |
|---|---|
| Your settings sheet | Only people who have its link (view only) |
| The sheet link | Nobody. It's stored as a hidden secret. |
| Your GitHub project | Anyone, but it only holds the program, not your data |
| Your job page | Anyone who has its address. It only shows matching jobs, and it asks search engines not to list it. |

---

*Open source, MIT license. JobScout reads the public job lists that companies publish on their
careers pages. It doesn't use LinkedIn or any paid service.*
