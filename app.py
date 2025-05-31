import streamlit as st
import subprocess
import os
import shutil

st.title("Pipeline automatizada de Mothur")

# Crear carpeta temporal
input_dir = "data"
if not os.path.exists(input_dir):
    os.makedirs(input_dir)

# Subir múltiples archivos FASTQ
uploaded_files = st.file_uploader("Sube tus archivos FASTQ", type=[
                                  "fastq"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"{len(uploaded_files)} archivos subidos.")
    for file in uploaded_files:
        file_path = os.path.join(input_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.read())

    # Botón para correr la pipeline
    if st.button("Ejecutar pipeline de Mothur"):
        # Construimos el comando completo
        mothur_commands = f"""
make.file(inputdir={input_dir}, type=fastq, prefix=stability)
make.contigs(file=stability.files)
summary.seqs(fasta=stability.trim.contigs.fasta, count=stability.contigs.count_table)
screen.seqs(fasta=stability.trim.contigs.fasta, count=stability.contigs.count_table, maxambig=0, minlength=420, maxlength=550, maxhomop=8)
unique.seqs(fasta=stability.trim.contigs.good.fasta, count=stability.contigs.good.count_table)
summary.seqs(count=stability.trim.contigs.good.count_table)
align.seqs(fasta=stability.trim.contigs.good.unique.fasta, reference=silva.bacteria.fasta)
summary.seqs(fasta=stability.trim.contigs.good.unique.align, count=stability.trim.contigs.good.count_table)
screen.seqs(fasta=stability.trim.contigs.good.unique.align, count=stability.trim.contigs.good.count_table, start=13144, end=25287, minlength=250, maxlength=500, maxambig=0, maxhomop=8)
summary.seqs(fasta=current, count=current)
filter.seqs(fasta=stability.trim.contigs.good.unique.good.align, vertical=T, trump=.)
unique.seqs(fasta=stability.trim.contigs.good.unique.good.filter.fasta, count=stability.trim.contigs.good.good.count_table)
pre.cluster(fasta=stability.trim.contigs.good.unique.good.filter.unique.fasta, count=stability.trim.contigs.good.unique.good.filter.count_table, diffs=2)
chimera.vsearch(fasta=stability.trim.contigs.good.unique.good.filter.unique.precluster.fasta, count=stability.trim.contigs.good.unique.good.filter.unique.precluster.count_table, dereplicate=t)
classify.seqs(fasta=stability.trim.contigs.good.unique.good.filter.unique.precluster.denovo.vsearch.fasta, count=stability.trim.contigs.good.unique.good.filter.unique.precluster.denovo.vsearch.count_table, reference=trainset9_032012.pds.fasta, taxonomy=trainset9_032012.pds.tax)
remove.lineage(fasta=stability.trim.contigs.good.unique.good.filter.unique.precluster.denovo.vsearch.fasta, count=stability.trim.contigs.good.unique.good.filter.unique.precluster.denovo.vsearch.count_table, taxonomy=stability.trim.contigs.good.unique.good.filter.unique.precluster.denovo.vsearch.pds.wang.taxonomy, taxon=Chloroplast-Mitochondria-unknown-Archaea-Eukaryota)
summary.tax(taxonomy=current, count=current)
rename.file(fasta=current, count=current, taxonomy=current, prefix=final)
cluster.split(fasta=final.fasta, count=final.count_table, taxonomy=final.taxonomy, taxlevel=4, cutoff=0.03)
make.shared(list=final.opti_mcc.list, count=final.count_table, label=0.03)
classify.otu(list=final.opti_mcc.list, count=final.count_table, taxonomy=final.taxonomy, label=0.03)
make.biom(shared=final.opti_mcc.shared, constaxonomy=final.opti_mcc.0.03.cons.taxonomy)
"""

        # Guardamos el archivo con comandos
        with open("mothur.batch", "w", encoding="utf-8") as f:
            f.write(mothur_commands)

        # Ejecutar Mothur
        comando = "mothur mothur.batch"
        st.write("Ejecutando pipeline completa...")
        try:
            resultado = subprocess.run(
                comando, shell=True, capture_output=True, text=True, check=True)
            st.success("Pipeline completada sin errores.")
        except subprocess.CalledProcessError as e:
            st.error("Hubo un error al ejecutar Mothur.")
            st.text_area("Salida de error:", e.stdout +
                         "\n" + e.stderr, height=600)

        st.text_area("Resultado:", resultado.stdout +
                     "\n" + resultado.stderr, height=600)

        # Opción para descargar resultados clave
        if os.path.exists("final.opti_mcc.shared"):
            with open("final.opti_mcc.shared", "rb") as f:
                st.download_button("Descargar archivo .shared",
                                   f, "final.opti_mcc.shared")
        if os.path.exists("final.opti_mcc.0.03.cons.taxonomy"):
            with open("final.opti_mcc.0.03.cons.taxonomy", "rb") as f:
                st.download_button("Descargar taxonomía",
                                   f, "final_taxonomy.txt")

        # Limpieza opcional
        shutil.rmtree(input_dir)
