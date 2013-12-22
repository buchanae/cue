pprint <- function(...) {

  convert <- function(f) {
    if (typeof(f) == "function" || typeof(f) == "closure") {
      f = do.call('paste0', as.list(deparse(f)))
    }
    return(toString(f))
  }

  args <- list(...)
  reprs <- lapply(args, convert)
  pasted <- do.call('paste', reprs)
  encoded <- encodeString(pasted)

  if (nchar(encoded) > 80) {
    trimmed <- strtrim(encoded, 77)
    out <- paste(trimmed, '...', sep='', collapse='')
  } else {
    out <- encoded
  }

  cat(out, sep='\n')
}


level.print <- function(level, ...) {
  pad <- paste0(rep('  ', level), collapse='')
  pprint(pad, ...)
}


walk <- function(node, level=0) {
  #level.print(level, typeof(node), node)
  #pprint('')
  type <- typeof(node)
  pprint(level)
  pprint(type)
  pprint(node)
  pprint('')

  if (type == "language" || type == "expression") {
    node <- as.list(node)

    for (part in node) {
      walk(part, level + 1)
    }
  }
}


#expr <- parse('call-by-name.r')
#expr <- parse(text='x <- 1L; y <- 1')

text <- "
x <- 1
y <- 2

foo <- function() {
  bar <- function(x) return(x + 1)

  y <- bar(5)

  if (1 == 2) {
    for (i in c(1, 2, 3)) {
    }
  }
  return(y + 3 + bar(6))
}
"

text <- "
x <- bar(5, 4)
"

text <- "
x <- 1 + 2 + 3 - 7

# comment
"

input <- file('stdin')
expr <- parse(input)
#expr <- parse(text=text)

walk(expr)
