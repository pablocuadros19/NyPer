#!/bin/bash
# Ejecutar antes de cambiar de cuenta.
# Valida que el handoff esté escrito y hace el commit.

echo ""
echo "=============================="
echo "   CIERRE DE SESION — NyPer"
echo "=============================="
echo ""

echo "--- Estado del repo ---"
git -C "$(dirname "$0")/.." status --short
echo ""

echo "Ya actualizaste CLAUDE_HANDOFF.md con el proximo paso concreto? (s/n)"
read -r ok_handoff
if [ "$ok_handoff" != "s" ]; then
  echo ""
  echo ">> Pedile a Claude:"
  echo "   'Actualizá el CLAUDE_HANDOFF.md con el estado actual."
  echo "    Incluí el próximo paso como instrucción específica con archivo y línea.'"
  echo ""
  echo "Cuando lo hayas hecho, volvé a correr este script."
  exit 1
fi

echo ""
echo "Es el segundo handoff del dia? (s/n)"
read -r segundo
if [ "$segundo" = "s" ]; then
  echo ""
  echo ">> TOPE DIARIO: no hagas mas cambios hoy."
  echo "   Termina la sesion y retoma mañana."
  echo ""
fi

echo ""
echo "Mensaje de commit (ej: feat: quitar filtro rubro en prospectos):"
read -r msg
cd "$(dirname "$0")/.." && git add . && git commit -m "$msg"

echo ""
echo "Commit hecho."
echo "Ahora: Sign Out en la extension de VS Code → Sign In con la otra cuenta."
echo ""
