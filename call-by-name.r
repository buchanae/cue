# A function call can be stored, which will then defer evaluation
print_call <- print("called")

print("start 1")

func <- function(arg1) {
  # Now the print_call that was passed in gets evaluated.
  print("func start")
  arg1
  print("func end")
}

func(print_call)

print("end 1")

# Nope, that didn't quite work. The call was stored, but I guess
# assignment doesn't defer evaluation.


print("start 2")

func(print("called"))

print("end 2")


print("start 3")

func <- function(x, expr=x*x) {
  return(expr)
}

print(func(3))

print("end 3")


print("start 4")

func <- function(x, y=z * z) {
  z = x + 1
  return (y)
}

print(func(2))

print("end 4")


print("start 5")

func <- function(y=1) {
  print(y)
  print(sys.frames())
}

funcB <- function() {
  print(environment())
  print(sys.frames())
  y = 5
  func()
}

funcB()

print("end 5")
