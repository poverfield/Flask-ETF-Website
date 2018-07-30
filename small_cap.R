
# Run weekdays at 6 pm

if (!require(BatchGetSymbols)) install.packages('BatchGetSymbols')
library(BatchGetSymbols)
library(TTR)


# Get DATA
# set dates
first.date <- Sys.Date() - 500
last.date <- Sys.Date()

# Retrive tickers
tickers = read.csv('sp-600-index.csv')[,1]
tickers = as.vector(tickers) # change to character
#tickers = tickers[1:20] # limit data to test on

# Query data
DATA_query <- BatchGetSymbols(tickers = tickers, 
                              first.date = first.date,
                              last.date = last.date, 
                              cache.folder = file.path(tempdir(), 
                                                       'BGS_Cache') ) # cache in tempdir()

x = nrow(DATA_query[[1]]) # define number of stocks analyzing

# get succesful ticker list from DATA_query[[1]] == 'keep'
S = matrix(data = NA, ncol = 1, nrow = x)
for(i in 1:x){
  if(DATA_query[[1]][i,6] == 'KEEP'){
    S[i] = toString(DATA_query[[1]][i,1])
  }
}
S = S[which(!is.na(S))] # remove NAs
x = length(S)
start_date = matrix(data = NA, ncol = x, nrow = 1)

DATA = list() #aggregate data into lists
for(i in 1:x){
  DATA[[i]] = DATA_query[[2]][which(DATA_query[[2]][,8] == S[i]),c(1:4,7)]
  if(DATA[[i]][nrow(DATA[[i]])-1,5] == DATA[[i]][nrow(DATA[[i]]),5]){
    DATA[[i]] = DATA[[i]][1:(nrow(DATA[[i]])-1),]
    print('Duplicate last date')
  }
  if(any(is.na(DATA[[i]]))){  # NAs = mean of t +/- 1
    na = which(is.na(DATA[[i]]), arr.ind = TRUE) # get NA locations (row, column)
    for(j in 1:nrow(na)){
      DATA[[i]][na[j,1], na[j,2]] = mean(c(DATA[[i]][na[j,1]-1, na[j,2]], DATA[[i]][na[j,1]+1, na[j,2]]))
    }
  }
  start_date[i] = DATA[[i]][1,5]
}
names(DATA) = S # name each df in list
# Unify lenghts -> have all matrices start at most recent start date
for(i in 1:x){
  if(start_date[i] != max(start_date)){
    DATA[[i]] = DATA[[i]][-1,]
  }
}

##Define Functions

# MACD function to return macd value (+ -> buy, - -> sell)
macd_func = function(DATA){
  # create macd table and column names
  macdseries = matrix(data = NA, ncol = length(S)*2, nrow = nrow(DATA[[1]]))
  macdnames = vector(length = ncol(macdseries)) #empty vector to name columns
  for(i in 1:length(S)){
    macdnames[2*i-1] = paste(S[i], "macd")
    macdnames[2*i] = paste(S[i], "Signal")
  }
  colnames(macdseries) = macdnames
  
  
  # fill table with macd
  for(i in 1:length(S)){
    macdseries[,c((2*i-1),2*i)] = MACD(DATA[[i]]$price.close, maType = 'EMA',percent = FALSE)
  }
  macdseries = na.omit(macdseries)
  macd = matrix(data = 0, ncol = length(S), nrow = nrow(macdseries)) # final macd buy signals
  even = seq(2, length(S)*2, by = 2) # even number for column id
  odd = seq(1,length(S)*2, by = 2) # odd
  for(i in 1:length(S)){
    for(j in 1:nrow(macdseries)){
      macd[j,i] = macdseries[j,odd[i]] - macdseries[j,even[i]] # if positive: signal > macd == buy
    }
  }
  return(macd)
}

rsi_func = function(DATA){
  rsi = matrix(data = NA, ncol = length(S), nrow = nrow(DATA[[1]]))
  for(i in 1:length(S)){
    rsi[,i] = RSI(DATA[[i]]$price.close, n = 14)
  }
  return(na.omit(rsi))
}

length_func = function(matrix, new_length){
  matrix = matrix[(nrow(matrix) - new_length + 1):nrow(matrix),]
  return(matrix)
}

buy_signal_func = function(DATA, j){
  df = DATA[[j]]
  nx = df[,5]
  buy = 0
  
  # find all macd cross overs that coincide with rsi < 50
  find_valley = function(macd,j){
    int = 0
    for(i in 2:nrow(macd)){
      if(macd[i-1,j] < 0 & macd[i,j] > 0){# & rsi[i,j] < 50){
        int = c(int, i)
      }
    }
    return(int)
  } 
  valley = find_valley(macd, j)
  
  
  #determine if divergence or not
  for(i in 3:length(valley)){
    if(min(macd[valley[i-2]:valley[i-1],j]) < min(macd[valley[i-1]:valley[i],j]) &
       min(df[valley[i-2]:valley[i-1],4]) > min(df[valley[i-1]:valley[i],4])){
      buy = c(buy,valley[i])
    }
  }
  return(buy)
}

signal_func = function(BUY){
  signal = 0
  for(i in 1:length(BUY)){
    signal = c(signal, max(BUY[[i]]))
  }
  signal = signal[-1]
  
  for(i in 1:length(S)){
    id = which(signal == nrow(DATA[[i]]))
  }
  return(id)
}

plot_func = function(id){
  if (length(id) > 0){
    for(i in 1:length(id)){
      name = names(DATA)[id[i]]
      png(filename = paste(name, '.png', sep=''))
      buy = BUY[[id[i]]]
      # plot
      plot(x = DATA[[id[i]]][,5], y = DATA[[id[i]]][,4], type = 'l', ylab = '$', xlab = 'date', main = name)
      abline(v = DATA[[id[i]]][,5][buy], col = 3, lty = 2)
      dev.off()
    }
    print('.png exported')
  } else {
    print('No .png to export')
  }
}

# STock Analysis
macd = macd_func(DATA) # create data table
rsi = rsi_func(DATA )

# unify lengths
new_length = min(nrow(macd), nrow(rsi))

macd = length_func(macd, new_length)
rsi = length_func(rsi, new_length)

# unify DATA length
for(i in 1:length(S)){
  DATA[[i]] = DATA[[i]][(nrow(DATA[[i]]) - new_length + 1):nrow(DATA[[i]]),]
}

# Buy signal
BUY = list()
for(i in 1:length(S)){
  BUY[[i]] = buy_signal_func(DATA, i)
}
signal = signal_func(BUY) # return only the signals to buy at next open
plot_func(signal)
