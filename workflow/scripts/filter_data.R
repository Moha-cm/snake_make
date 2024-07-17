library(dplyr)

file <- read.csv("snakemake@input[[1]")

filter <- file %>%
  filter(Gene_name == "FOLR1")

write.csv(filter, file = "snakemake@output[[1]]")