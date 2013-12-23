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
  pprint('.level', level)
  pprint('.type', type)

  if (type == "language" || type == "expression") {
    pprint('')

    # Discard the return value
    f <- lapply(node, walk, level + 1)

  } else if (type == "pairlist") {

    output_pairlist <- function(name, value) {
      pprint('.argname', name)
      pprint('.argvalue', value)
      pprint('.argtype', typeof(value))
    }
    mapply(output_pairlist, names(node), node)
    pprint('')

  } else {
    pprint('.content', node)
    pprint('')
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


text <- "
foo <- function() 1
function(x, bar=foo, gz=2) 100
x + 1
"

# TODO this is an important case to consider
#      `row.names(x) <- value`
#      http://stat.ethz.ch/R-manual/R-devel/library/base/html/row.names.html
#      I'm not sure how that works, and assigning to a function call seems
#      very unintuitive to me.
#      http://www.johnmyleswhite.com/notebook/2009/12/14/object-oriented-programming-in-r-the-setter-methods/


#input <- file('stdin')
#expr <- parse(input)
expr <- parse(text=text)

walk(expr)
