\LoadClass[a4paper,12pt]{article} % Classe du document

%======================================================
% PACKAGES DE BASE (langue, encodage, math, graphique)
%======================================================
\RequirePackage[french]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathtools, amsmath, amssymb}
\RequirePackage{siunitx}
\RequirePackage{graphicx}
\RequirePackage{float}
\RequirePackage[section]{placeins}
\RequirePackage[left=2cm,right=2cm,top=2cm,bottom=2.5cm]{geometry}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{url}
\RequirePackage{lipsum}
\RequirePackage{enumitem}
\usepackage{bookmark}
\RequirePackage{tabularx}
\usepackage{array}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{pdflscape}
\usepackage{longtable}
\usepackage{ltablex}
\numberwithin{figure}{section}
\usepackage{amsmath}


%======================================================
% POLICES ET TAILLES
%======================================================
\RequirePackage{fix-cm}
\RequirePackage{lmodern}

%======================================================
% COULEURS
%======================================================
\RequirePackage{xcolor}
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}
\definecolor{mygreen}{RGB}{28,172,0}
\definecolor{mylilas}{RGB}{170,55,241}
\definecolor{orangeAM}{RGB}{255,163,0}
\definecolor{violetAM}{RGB}{128,39,108}

%======================================================
% LISTINGS & CODE
%======================================================
\RequirePackage{listings}

\lstdefinelanguage{VHDL}{
  morekeywords={
      library,use,all,entity,is,port,in,out,end,architecture,of,begin,
      and,or,signal,process,if,then,else,elsif,wait,until,rising_edge,
      event,when,others,case,loop,while,for,generate,downto,to,with,select
    },
  sensitive=false,
  morecomment=[l]--,
  morestring=[b]"
}

\lstdefinestyle{defaultstyle}{
  backgroundcolor=\color{backcolour},
  basicstyle=\ttfamily\small,
  keywordstyle=\color{blue}\bfseries,
  commentstyle=\color{green!50!black}\itshape,
  stringstyle=\color{orange},
  numbers=left,
  numberstyle=\tiny\color{codegray},
  stepnumber=1,
  numbersep=5pt,
  frame=single,
  breaklines=true,
  captionpos=t,
  showstringspaces=false,
  tabsize=2
}

\lstdefinestyle{vhdlstyle}{
  style=defaultstyle,
  language=VHDL
}

\lstset{style=defaultstyle}

%======================================================
% OUTILS DE MISE EN PAGE
%======================================================
\RequirePackage{fancybox}
\RequirePackage{thmbox}
\RequirePackage{fancyhdr}
\RequirePackage{wallpaper}
\RequirePackage{nomencl}
\RequirePackage{picinpar}
\RequirePackage{mathabx}
\RequirePackage{soul}
\RequirePackage{multirow}
\RequirePackage{lastpage}
\RequirePackage{nopageno}
\RequirePackage{wrapfig}
\RequirePackage{colortbl}
\RequirePackage{tocbasic}
\RequirePackage{sectsty}
\RequirePackage{comment}
\RequirePackage{indentfirst}
\RequirePackage{titlesec}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{tocloft}

%======================================================
% TIKZ & CIRCUITS
%======================================================
\RequirePackage{pgf,tikz}
\usetikzlibrary{automata, positioning, arrows, babel}
\usepackage[european]{circuitikz}
\RequirePackage{tkz-tab}

\usepackage{etoolbox} % déjà chargé
\usepackage[toc,acronym,hyperfirst=true]{glossaries}
\makeglossaries

% Compteur pour les indices
\newcounter{glossnote}
\setcounter{glossnote}{0}

% Commande robuste pour un terme de glossaire avec indice
\DeclareRobustCommand{\gloss}[1]{%
  \gls{#1}\textsuperscript{\refstepcounter{glossnote}\theglossnote}%
}

% Commande robuste pour le pluriel
\DeclareRobustCommand{\glosspl}[1]{\glspl{#1}}

% STYLE PERSONNALISÉ POUR LE GLOSSAIRE %
\newglossarystyle{monglossairestyle}{%
  % Ne pas hériter du style 'long' (il produit des séparateurs d'alignement
  % comme & dans le fichier .gls). Utiliser 'list' qui est compatible avec
  % l'environnement 'description' défini ci-dessous.
  \setglossarystyle{list} % Style de base (liste simple)
  \renewenvironment{theglossary}{%
    \begin{description}%
      }{%
    \end{description}%
  }%
  \renewcommand*{\glossentry}[2]{%
    \item[\glsentryitem{##1}\glstarget{##1}{\glossentryname{##1}}]%
    \glossentrydesc{##1}\glspostdescription\space ##2%
    \par\vspace{1.5\baselineskip} % Espace entre chaque définitions
  }%
}

% Appliquer le style personnalisé
\setglossarystyle{monglossairestyle}

%======================================================
% TAILLES DE TEXTE ET TITRES
%======================================================
\renewcommand\normalsize{\fontsize{12}{18}\selectfont}

% {⟨indent⟩}{⟨before⟩}{⟨after⟩} %
\titleformat{\section}{\fontsize{20}{22}\bfseries}{\thesection}{1em}{}
\titlespacing*{\section}{0pt}{0pt}{25pt}

\titleformat{\subsection}{\fontsize{16}{20}\bfseries}{\thesubsection}{1em}{}
\titlespacing*{\subsection}{0pt}{30pt}{10pt}

\titleformat{\subsubsection}{\fontsize{14}{16}\bfseries}{\thesubsubsection}{1em}{}
\titlespacing*{\subsubsection}{0pt}{30pt}{20pt}

%======================================================
% SOMMAIRE : TOCLOFT
%======================================================
\setlength{\cftbeforesecskip}{0.5em}
\setlength{\cftbeforesubsecskip}{0.3em}
\setlength{\cftsecnumwidth}{2.5em}
\setlength{\cftsubsecnumwidth}{3em}
\setlength{\cftaftertoctitleskip}{2em}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\renewcommand{\cftsubsecleader}{\cftdotfill{\cftdotsep}}

%======================================================
% TABLES DES FIGURES
%======================================================
\pagestyle{fancy}
\setlength{\cftbeforefigskip}{0.5em}
\setlength{\cftfignumwidth}{3em}
\renewcommand{\cftfigleader}{\cftdotfill{\cftdotsep}}
\setlength{\cftafterloftitleskip}{2em}

%======================================================
% COMMANDES UTILISATEUR (rapport)
%======================================================
\newcommand{\espace}{\vspace{0.2cm}}
\newcommand{\ecole}[1]{\renewcommand{\ecole}{#1}}
\newcommand{\periode}[1]{\renewcommand{\periode}{#1}}
\newcommand{\titre}[1]{\renewcommand{\titre}{#1}}
\newcommand{\enseignant}[1]{\renewcommand{\enseignant}{#1}}
\newcommand{\tuteur}[1]{\renewcommand{\tuteur}{#1}}
\newcommand{\eleve}[1]{\renewcommand{\eleve}{#1}}
\newcommand{\etudiantone}[1]{\renewcommand{\etudiantone}{#1}}
\newcommand{\etudianttwo}[1]{\renewcommand{\etudianttwo}{#1}}

%======================================================
% PIEDS DE PAGE ET NUMÉROTATION
%======================================================
\newcommand{\totalpages}{%
  \ifnum\getpagerefnumber{LastPage}>0
    \getpagerefnumber{LastPage}%
  \else
    ?%
  \fi
}

\fancypagestyle{plain}{
  \fancyhf{}
  \lhead{\includegraphics[scale=0.2]{images/logos/entete_deux_logos.png}}
  \rhead{\text{October 2025}}
  \cfoot{Page \thepage\ sur \pageref{LastPage}}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0.4pt}
}

\newcommand{\fairemargesintro}{
  \pagestyle{fancy}
  \fancyheadoffset{1cm}
  \setlength{\headsep}{1.5cm}
  % \setlength{\headheight}{1cm}
  \lhead{\includegraphics[scale=0.2]{images/logos/entete_deux_logos.png}}
  \rhead{\text{Septembre 2025}}
  \cfoot{}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0.4pt}
}

\newcommand{\fairemarges}{
  \pagestyle{fancy}
  \fancyheadoffset{1cm}
  \setlength{\headsep}{1.5cm}
  % \setlength{\headheight}{1.5cm}
  \lhead{\includegraphics[scale=0.2]{images/logos/entete_deux_logos.png}}
  \rhead{\text{Septembre 2025}}
  \cfoot{Page \thepage\ sur \pageref{LastPage}}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0.4pt}
}

%======================================================
% PAGE DE GARDE
%======================================================

% --- Définition du style vide pour la première page ---
\fancypagestyle{emptyfirstpage}{
  \fancyhf{} % supprime tout contenu d'en-tête et pied
  \renewcommand{\headrulewidth}{0pt} % supprime la ligne d'en-tête
  \renewcommand{\footrulewidth}{0pt} % supprime la ligne de pied
}

\newcommand{\fairepagedegarde}{
  \begin{titlepage}
    \begin{HeaderBox}
      % Logos sur la même ligne
      \begin{minipage}{0\textwidth}
        \raggedleft
        \includegraphics[height=1.5cm]{images/logos/POLYTECH_NANTES.png}
      \end{minipage}%
      \hfill
      \begin{minipage}{0.14\textwidth}
        \raggedright
        \includegraphics[height=1.5cm]{images/logos/Logo_mairie_saint_mars_du_desert.png}
      \end{minipage}

      \centering
      \vspace{1cm} % espace entre les logos et le titre
      {\huge\bfseries Cahier Des Charges}\\[5pt]
      \vspace{10pt}
    \end{HeaderBox}

    \thispagestyle{emptyfirstpage}
    \centering
    \vspace{90pt}
    {\Huge \itshape \textbf{Nom du projet :} \\[10pt]
      \textit{Collecteurs de données animalières}} \\[50pt]
    \rule{0.5\textwidth}{0.4pt} \\[5pt]
    {\normalsize
    \textbf{Version du document :} \\[3pt]
    \textit{n°1} \\[15pt]
    \textbf{Date du document :} \\[3pt]
    \textit{18/10/2025} \\[15pt]
    \textbf{Client :} \\[3pt]
    \textit{Xavier Leprevost} \\[15pt]
    \textbf{Auteurs :} \\[3pt]
    \textit{Ewen Le Callet} \\
    \textit{Xueying Xu} \\
    \textit{Davy Clark} \\
    \textit{Jules Noumba} \\
    \textit{Nolan Buchet} \\
    \textit{Joris Menard} \\
    }
    \rule{0.5\textwidth}{0.4pt}
  \end{titlepage}
}



%======================================================
% FIGURES
%======================================================
\newcommand{\insererfigure}[4]{
  \begin{figure}[ht]
    \centering
    \includegraphics[height=#2]{#1}
    \caption{#3}
    \label{fig:#4}
  \end{figure}
}
\numberwithin{figure}{section}

\renewcommand{\arraystretch}{1.3} % espace vertical entre lignes
\setlength{\tabcolsep}{4pt}       % espace horizontal entre colonnes

%======================================================
% CADRES
%======================================================
\usepackage{mdframed}

\newmdenv[
  topline=true, bottomline=true, leftline=true, rightline=true,
  linewidth=0.8pt, linecolor=black, backgroundcolor=white,
  innertopmargin=8pt, innerbottommargin=8pt,
  innerleftmargin=10pt, innerrightmargin=10pt
]{HeaderBox}

\newmdenv[
  backgroundcolor=gray!12, linecolor=gray!40,
  linewidth=0.5pt, innertopmargin=8pt, innerbottommargin=8pt,
  innerleftmargin=10pt, innerrightmargin=10pt
]{NoteBox}