library("ggplot2")


ComparisonPageRank2Qrel <- read.csv("/Users/jan/Nextcloud/Uni/Master/AdvancedInformationRetrival/touche/PageRank/res/ComparisonPageRank2Qrel.csv")
#plot(ComparisonPageRank2Qrel$QrelScore,ComparisonPageRank2Qrel$pagerank)

lower <-asquantile(ComparisonPageRank2Qrel$pagerank,0.25)
upper <-quantile(ComparisonPageRank2Qrel$pagerank,0.75)

cor(ComparisonPageRank2Qrel$QrelScore,ComparisonPageRank2Qrel$pagerank,method = "spearman")
ggplot(ComparisonPageRank2Qrel, aes(x=as.factor(QrelScore), y=pagerank)) + geom_boxplot(fill="slateblue") + xlab("Qrel Score")+ ylab("PageRank") +    geom_jitter(color="black",size=0.3)

ggplot(ComparisonPageRank2Qrel, aes(x=as.factor(trunc(pagerank)), y=ChatNoirScore)) + geom_boxplot(fill="slateblue") + xlab("PageRank")+ ylab("ChatNoir") +    geom_jitter(color="black",size=0.3)
