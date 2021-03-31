library("ggplot2")


training <- read.csv("~/Nextcloud/Uni/Master/AdvancedInformationRetrival/touche/SVM/res/training.csv")
training$Prediction <- as.numeric(gsub("\\[|\\]", "", training$Prediction))

cor(training$QrelScore,training$Prediction,method = "spearman")
cor(training$QrelScore,training$ChatNoirScore,method = "spearman")
cor(training$Prediction,training$ChatNoirScore,method = "spearman")

ggplot(training, aes(x=as.factor(QrelScore), y=Prediction)) + 
      geom_boxplot(fill="slateblue") + 
      xlab("Qrel Score")+ ylab("Prediction") + 
      geom_jitter(color="black",size=0.3)
