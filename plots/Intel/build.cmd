pdflatex critical_throughput.tex 
pdflatex critical_throughput.tex 
pdflatex parallel_throughput.tex
pdflatex parallel_throughput.tex

for /d %%i in (*) do (
  pushd %%i
  for %%j in (*.tex) do (
    pdflatex %%j 
    pdflatex %%j
  )
  popd
)