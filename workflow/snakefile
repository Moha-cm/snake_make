rule filter_gene:
    input:
        "data_set/ensembl_gene_ids.csv"
    output:
        "output/filter_gene_ids.csv"
    conda:
        "envs/R_env.yaml"
    script:
        "scripts/filter.R"

