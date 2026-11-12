---
name: conventional-commit
description: Genera mensajes de commit con el formato Conventional Commits a partir del diff. Se usa cuando el usuario pide commitear, hacer un commit o guardar cambios en Git.
---

# Conventional Commit

Cuando generes un mensaje de commit:

1. Antes de elegir nada, mirá `git status` y `git diff --staged` (si no hay nada preparado, `git diff`).
2. Elegí el tipo según lo que cambió:
   - `feat`: funcionalidad nueva
   - `fix`: corrección de un error
   - `docs`: documentación (PRD, README, AGENTS.md)
   - `chore`: mantenimiento o configuración (.gitignore, dependencias)
   - `refactor`: cambio de código que no cambia el comportamiento
   - `test`: tests
3. Formato: `tipo(alcance): descripción`
   - El alcance es opcional y dice qué parte toca (ej.: `PRD`, `skills`, `readme`).
   - La descripción va con el verbo en infinitivo y en español ("agregar", "corregir"), en minúscula, sin punto final y con 72 caracteres como máximo.
4. Si el diff mezcla cambios de distinto tipo, proponé separarlos en varios commits, uno por tipo.

Ejemplo: `feat(skills): agregar skill create-prd para crear y auditar PRDs en loop`
