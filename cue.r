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
  level.print(level, typeof(node), node)
  pprint('')

  if (typeof(node) == "language" || typeof(node) == "expression") {
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
  return(y + 3 + bar(6))
}
"

expr <- parse(text=text)

walk(expr)
