master_data <- read.csv("DVA-Project/Transformers/tables/master_table.csv")
#colnames(master_data)
# remove 'type' column for lm function to work
master_data <- subset(master_data, select = -type)

# use lm function for modeling the dependent variables = units_sold_lowerbound, units_sold, and units_sold_upperbound
# remove steam_appid, name, and total_reviews from the independent variables list
# also need to remove controller_support_full and review_score_9.0 as those are already in the intercept
model_log <- lm(log(total_reviews + 1) ~. -steam_appid -name -units_sold_lowerbound -units_sold -units_sold_upperbound -controller_support_full - review_score_9.0, data=master_data)
summary(model_log)

# when performing predictions, we need to turn the predictions back into real numbers - not log form
# then multiply this by the thresholds from the python script; 30->base +/- 15

# Get the coefficients, intercept, and slopes
coefs <- stack(coef(model_log))
coefs <- coefs[, c("ind", "values")]
coefs
write.csv(coefs, "DVA-Project/Algorithms/model_coefficients.csv", row.names = FALSE)
