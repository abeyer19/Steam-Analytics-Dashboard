# 0. Install and Load Packages
#install.packages("car")
#install.packages("DT")
library(car)
library(DT)

# 1. Import Data
master_data <- read.csv("DVA-Project/Transformers/tables/master_table.csv")
colnames(master_data)

# 2. Truncate Data
## remove 'type' column, as all are games
## get x_test and y_test
master_data <- subset(master_data, select = -c(steam_appid, name, type, is_free))

# 3. Train Linear Regression Model
## use lm function for modeling the dependent variable = total_reviews
## take log() of total reviews for normalization of outliers
## remove steam_appid, name, and total_reviews from the independent variables list
model_log <- lm(log(total_reviews + 1) ~. -total_reviews, data=master_data)
summary(model_log)


#################################################################################################################

# when performing predictions, we need to turn the predictions back into real numbers - not log form
# then multiply this by the thresholds from the python script for revenue; Units Sold = (30 +/-15) * exp(reviews)

#################################################################################################################


# 4. Get the coefficients, intercept, and slopes
coefs <- stack(coef(model_log))
coefs <- coefs[, c("ind", "values")]
coefs
#write.csv(coefs, "DVA-Project/Algorithms/model_coefficients.csv", row.names = FALSE)


# 5. Check VIF (multicollinearity)
# convert VIF vector to a matrix/dataframe, get the top 15 variables, and print in a datatable
vif_vals <- vif(model_log)
vif_matrix <- data.frame(Variable = names(vif_vals), VIF_Score = as.numeric(vif_vals))
colnames(vif_matrix) <- c("Variable_Name", "VIF_Score")
datatable(vif_matrix, options = list(order = list(list(2, 'desc')), pageLength = 15))

# get the top 15 VIF variables and print in a datatable
top_15_vif <- head(vif_matrix[order(-vif_matrix$VIF_Score), ], 15)
top_15_vif
selected_data <- master_data[, top_15_vif$Variable_Name]
numeric_data <- sapply(selected_data, as.numeric)
cor_matrix <- round(cor(numeric_data, use = "pairwise.complete.obs"), 3)
datatable(cor_matrix, options = list(scrollX = TRUE, pageLength = 15), filter = 'top')

# get pairs of variables with correlations above 75% from VIF
cor_pairs <- as.data.frame(as.table(cor_matrix))
high_cor <- subset(cor_pairs, Freq > 0.75 & as.character(Var1) < as.character(Var2))
high_cor <- high_cor[order(-high_cor$Freq), ]
colnames(high_cor) <- c("Variable_1", "Variable_2", "Correlation")
high_cor


# 6. Remove high VIF variables from master_data
cols_to_drop <- unique(as.character(high_cor$Variable_2))
master_data_vif <- master_data[, !(names(master_data) %in% cols_to_drop)]


# 7. Rerun the lm model and get coefficients
model_log_vif <- lm(log(total_reviews + 1) ~. -total_reviews, data=master_data_vif)
summary(model_log_vif)

coefs <- stack(coef(model_log_vif))
coefs <- coefs[, c("ind", "values")]
coefs
#write.csv(coefs, "DVA-Project/Algorithms/model_coefficients.csv", row.names = FALSE)
