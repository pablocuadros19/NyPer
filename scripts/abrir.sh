#!/bin/bash
# Ejecutar al abrir sesion con la cuenta entrante.
# Mostrar handoff + ultimos commits + prompt listo para copiar.

ROOT="$(dirname "$0")/.."

echo ""
echo "=============================="
echo "   APERTURA DE SESION — NyPer"
echo "=============================="
echo ""

echo "--- Ultimos 5 commits ---"
git -C "$ROOT" log --oneline -5
echo ""

echo "--- HANDOFF ACTUAL ---"
echo ""
cat "$ROOT/CLAUDE_HANDOFF.md"
echo ""

echo "--- TASKS PENDIENTES ---"
echo ""
grep -A 20 "## En curso" "$ROOT/TASKS.md" | head -20
echo ""

echo "=============================="
echo "  PROMPT DE ARRANQUE — copiar y pegar a Claude:"
echo "=============================="
echo ""
cat "$ROOT/prompts/arranque.txt"
echo ""
