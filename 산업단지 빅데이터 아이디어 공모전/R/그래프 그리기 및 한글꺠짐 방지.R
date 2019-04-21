library(ggplot2)
library(readxl)
library(dplyr)
library(ggthemes)
par(family = “Nanumgothic”)



install.packages("extrafont")
library(extrafont)
font_import()
y
cairo_pdf("Rplot_font_adjust.pdf", family= "Nanumgothic")

index_final <- read_excel("final.xlsx",sheet = 4)
View(index_final)

ggplot(data = index_final, aes(x = 화재피해지수, y = 화재진압지연지수,)) +
    xlim(0,100) +
    ylim(0,100) +
    geom_point(shape=20, size=3, colour="blue") +
    ggtitle("산점도 그래프") +
    geom_hline(yintercept=50, colour="red", linetype = 2) +
    geom_vline(xintercept=50, colour="red", linetype = 2)  +
    theme_bw(base_family = "AppleGothic")


    

  
 

