# ============================
#   Makefile — Projet CDC
# ============================

# Nom principal du document (sans extension)
MAIN = main

# Commandes
LATEX = pdflatex
MAKEGLOSSARIES = makeglossaries
RM = rm -f

# Options
LATEX_OPTS = -interaction=nonstopmode -shell-escape

# Règle par défaut : compiler le PDF
all: $(MAIN).pdf

# ----------------------------
# Étapes de compilation
# ----------------------------
$(MAIN).pdf: $(MAIN).tex $(wildcard text/*.tex) $(wildcard images/**/*.png) param.cls
	@echo "=== Compilation LaTeX 1/3 ==="
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex

	@echo "=== Génération du glossaire ==="
	$(MAKEGLOSSARIES) $(MAIN)

	@echo "=== Compilation LaTeX 2/3 ==="
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex

	@echo "=== Compilation LaTeX 3/3 ==="
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex

	@echo "✅ PDF généré : $(MAIN).pdf"

# ----------------------------
# Nettoyage des fichiers temporaires
# ----------------------------
clean:
	@echo "🧹 Suppression des fichiers temporaires..."
	$(RM) $(MAIN).aux $(MAIN).log $(MAIN).lof $(MAIN).lot \
	      $(MAIN).fls $(MAIN).out $(MAIN).toc $(MAIN).fmt \
	      $(MAIN).fot $(MAIN).cb $(MAIN).cb2 $(MAIN).glo \
	      $(MAIN).gls $(MAIN).glg $(MAIN).glsdefs $(MAIN).ist \
	      $(MAIN).acn $(MAIN).acr $(MAIN).alg $(MAIN).bbl $(MAIN).blg \
	      $(MAIN).run.xml $(MAIN).fdb_latexmk \
		  $(MAIN).synctex.gz \ 
		  indent.log 
	@echo "✅ Nettoyage terminé."

# ----------------------------
# Nettoyage complet (inclut le PDF)
# ----------------------------
mrproper: clean
	@echo "🧨 Suppression du PDF final..."
	$(RM) $(MAIN).pdf
	@echo "✅ Dossier propre."

# ----------------------------
# Aide
# ----------------------------
help:
	@echo ""
	@echo "📘 Commandes disponibles :"
	@echo "  make          → Compile le projet et génère main.pdf"
	@echo "  make clean    → Supprime les fichiers temporaires LaTeX"
	@echo "  make mrproper → Supprime les fichiers temporaires + le PDF"
	@echo "  make help     → Affiche cette aide"
	@echo ""

.PHONY: all clean mrproper help

# make : Compile main.tex → produit main.pdf
# make : clean	Supprime tous les fichiers temporaires LaTeX
# make : mrproper	Supprime aussi le PDF final
# make : help	Affiche un résumé des commandes