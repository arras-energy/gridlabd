import os, sys

target = "../html"
contents = "../html/toc.html"

os.makedirs(target,exist_ok=True)
toc = open(contents,'w')

def convert(path,n=1):
	os.makedirs(os.path.join(target,path),exist_ok=True)
	toc.write(f"<H{n}>{os.path.basename(path).title()}</H{n}>\n<UL>\n")
	for file in sorted(os.listdir(path)):
		if file[0] in ["_","."]:
			continue
		elif file.endswith(".md"):
			inf = f"{path}/{file}"
			outf = f"{path.replace(".",target)}/{file.replace('.md','.html')}"
			if not os.path.exists(outf) or os.path.getmtime(inf) > os.path.getmtime(outf):
				os.system(f"""pandoc "{inf}" -o "{outf}" """)
			toc.write(f"""<LI><A HREF="{outf}" TARGET="PAGE">{os.path.splitext(os.path.basename(file).replace('_',' '))[0]}</A></LI>\n""")
		elif os.path.isdir(file):
			convert(os.path.join(path,file),n+1)
	toc.write("</UL>\n")

if __name__ == "__main__":
	convert(".")