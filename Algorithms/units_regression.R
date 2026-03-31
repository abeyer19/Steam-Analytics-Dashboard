master_data <- read.csv('Transformers/tables/master_table.csv')
#colnames(master_data)
# remove 'type' column for lm function to work
master_data <- subset(master_data, select = -type)

# use lm function for modeling the dependent variables = units_sold_lowerbound, units_sold, and units_sold_upperbound
# remove steam_appid, name, and total_reviews from the independent variables list
model_log <- lm(log(total_reviews + 1) ~. -steam_appid -name -units_sold_lowerbound -units_sold -units_sold_upperbound, data=master_data)
summary(model_log)

# when performing predictions, we need to turn the predictions back into real numbers - not log form
# then multiply this by the thresholds from the python script; 30->base +/- 15
#log_preds <- predict.lm()
#real_preds <- exp(log_preds + (summary(model_log)$sigma^2 / 2))

#estimated_units_sold <- real_preds * 30
#estimated_units_sold_lowerbound  <- real_preds * 15
#estimated_units_sold_upperbound  <- real_preds * 45
