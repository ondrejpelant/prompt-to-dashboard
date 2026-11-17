---
tags: [jak-to-funguje]
---
# Git

Zpět na [[00 Start]] · Příkazy v [[Tahák příkazů]]

Git je **ukládání pozice ve hře**.

- Píšeš kód (hraješ). Když je to dobré, **uložíš pozici** s popiskem → **commit**.
- Na staré pozice se můžeš podívat nebo se k nim vrátit → `git log`, `git restore`.
- Před uložením vybereš, co do pozice patří → **staging**, `git add`.
- **GitHub** je cloud se zálohou pozic. Odeslání = **push**, stažení = **pull**.
- **`.gitignore`** je seznam věcí, které se nikdy neukládají: hesla (`.env`), data, `.venv`.

```text
změníš soubory  →  git add  →  git commit  →  git push
  (hraješ)          (vybereš)    (uložíš)        (zálohuješ)
```

## Co jsem se naučil

- `git status` ukazuje červeně „změněno, nevybráno“ a zeleně „vybráno do commitu“.
- `.env` v `git status` nikdy neuvidím – je v `.gitignore`.
- Při `git commit` běží kontroly z pre-commitu → [[Kontroly kvality]].
- Ve výpisu `git push` znamená `eb8b5c9..d3db58d  main -> main`, že se `main` na GitHubu posunul na můj commit.
- Popisek commitu: anglicky, rozkazovací způsob, do 50 znaků – „Pin Metabase to v0.64.3.1“.
