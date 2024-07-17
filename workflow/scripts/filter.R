library(dplyr)

# Read input fil
file <- read.csv(snakemake@input[[1]])

# Filter based on Gene_name == "FOLR1"
filter <- file %>%
  filter(Gene_name == "FOLR1")

# Write filtered data to output file
write.csv(filter, file = snakemake@output[[1]], row.names = FALSE)
