#!/usr/bin/env python

if hasattr(__builtins__, 'xrange'):
	range = xrange

class Expr(object):
	__slots__ = ()
	def str_under(self,precedence):
#		return '(%s)' % str(self)
		if precedence > self.precedence:
			return '(%s)' % str(self)
		else:
			return str(self)

	def annot_str_under(self,annot_map,precedence):
#		return '(%s)' % self.annot_str(annot_map)
		if precedence > self.precedence:
			return '(%s)' % self.annot_str(annot_map)
		else:
			return self.annot_str(annot_map)

class BinExpr(Expr):
	__slots__ = 'left', 'right', 'value', 'used', 'generation'
	def __init__(self, left, right, value, generation):
		self.left  = left
		self.right = right
		self.value = value
		self.used  = left.used | right.used
		self.generation = generation

	def __hash__(self):
		return hash((self.__class__, self.left, self.right))

	def __eq__(self, other):
		if type(self) is not type(other):
			return False

		return self.left == other.left and self.right == other.right
	
	def numeric_hash(self):
		return hash((self.__class__, self.left.numeric_hash(), self.right.numeric_hash()))
	
	def numeric_eq(self, other):
		if type(self) is not type(other):
			return False

		return self.left.numeric_eq(other.left) and self.right.numeric_eq(other.right)
	
class Add(BinExpr):
	__slots__ = ()
	def __init__(self, left, right, generation):
		BinExpr.__init__(self, left, right, left.value + right.value, generation)

	def __str__(self):
		p = self.precedence
		return '%s + %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self, annot_map):
		p = self.precedence
		return '%s + %s' % (
			self.left.annot_str_under(annot_map, p),
			self.right.annot_str_under(annot_map, p))

	precedence = property(lambda self: 0)

class Sub(BinExpr):
	__slots__ = ()
	def __init__(self, left, right, generation):
		BinExpr.__init__(self, left, right, left.value - right.value, generation)

	def __str__(self):
		p = self.precedence
		return '%s - %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self, annot_map):
		p = self.precedence
		return '%s - %s' % (
			self.left.annot_str_under(annot_map, p),
			self.right.annot_str_under(annot_map, p))
	
	precedence = property(lambda self: 1)
		
class Mul(BinExpr):
	__slots__ = ()
	def __init__(self, left, right, generation):
		BinExpr.__init__(self, left, right, left.value * right.value, generation)
		
	def __str__(self):
		p = self.precedence
		return '%s * %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self, annot_map):
		p = self.precedence
		return '%s * %s' % (
			self.left.annot_str_under(annot_map, p),
			self.right.annot_str_under(annot_map, p))

	precedence = property(lambda self: 3)

class Div(BinExpr):
	__slots__ = ()
	def __init__(self, left, right, generation):
		BinExpr.__init__(self, left, right, left.value // right.value, generation)
	
	def __str__(self):
		p = self.precedence
		return '%s / %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self, annot_map):
		p = self.precedence
		return '%s / %s' % (
			self.left.annot_str_under(annot_map, p),
			self.right.annot_str_under(annot_map, p))

	precedence = property(lambda self: 2)

class Val(Expr):
	__slots__ = 'value', 'used', 'index', 'generation'
	def __init__(self, value, index, generation):
		self.value = value
		self.index = index
		self.used  = 1 << index
		self.generation = generation
	
	def __str__(self):
		return str(self.value)

	def str_under(self, precedence):
		return str(self.value)

	def annot_str(self, annot_map):
		return str(self.value) + ("'" * annot_map[self.index])

	def annot_str_under(self, annot_map, precedence):
		return self.annot_str(annot_map)

	def __hash__(self):
		return self.index

	def __eq__(self, other):
		if type(self) is not type(other):
			return False

		return self.index == other.index

	def numeric_hash(self):
		return self.value

	def numeric_eq(self, other):
		if type(self) is not type(other):
			return False

		return self.value == other.value

	precedence = property(lambda self: 4)

class NumericHashedExpr(object):
	__slots__ = 'expr', '__hash'
	def __init__(self,expr):
		self.expr = expr
		self.__hash = expr.numeric_hash()
	
	def __hash__(self):
		return self.__hash

	def __eq__(self,other):
		return self.expr.numeric_eq(other.expr)

def is_normalized_add(left, right):
	rt = type(right)
	if rt is Add or rt is Sub:
		return False

	lt = type(left)
	if lt is Add:
		return left.right.value <= right.value
	elif lt is Sub:
		return False
	else:
		return left.value <= right.value

def is_normalized_sub(left, right):
	rt = type(right)
	if rt is Add or rt is Sub:
		return False

	lt = type(left)
	if lt is Sub:
		return left.right.value <= right.value
	else:
		return True

def is_normalized_mul(left, right):
	rt = type(right)
	if rt is Mul or rt is Div:
		return False

	lt = type(left)
	if lt is Mul:
		return left.right.value <= right.value
	elif lt is Div:
		return False
	else:
		return left.value <= right.value

def is_normalized_div(left, right):
	rt = type(right)
	if rt is Mul or rt is Div:
		return False

	lt = type(left)
	if lt is Div:
		return left.right.value <= right.value
	else:
		return True

def solutions(target, numbers):
	numcnt = len(numbers)
	full_usage = ~(~0 << numcnt)
	segments = [[] for _ in range(full_usage)]

	generation = 0
	exprs = []

	has_single_number_solution = False
	for i, num in enumerate(numbers):
		expr = Val(num, i, generation)
		if num == target:
			if not has_single_number_solution:
				has_single_number_solution = True
				yield expr
		else:
			exprs.append(expr)
			segments[expr.used - 1].append(expr)

	uniq_solutions = set()

	lower = 0
	upper = numcnt
	while lower < upper:
		prev_generation = generation
		generation += 1
		for b in range(lower, upper):
			bexpr = exprs[b]
			bused = bexpr.used

			for aused in range(1, full_usage + 1):
				if (bused & aused) == 0:
					segment = segments[aused - 1]
					for aexpr in segment:
						if aexpr.generation == prev_generation:
							it = make_half(aexpr, bexpr, generation)
						else:
							it = make(aexpr, bexpr, generation)
						for expr in it:
							if expr.value == target:
								wrapped = NumericHashedExpr(expr)
								if wrapped not in uniq_solutions:
									uniq_solutions.add(wrapped)
									yield expr
							elif expr.used != full_usage:
								exprs.append(expr)
								segments[expr.used - 1].append(expr)
		lower = upper
		upper = len(exprs)

def make_half(a, b, generation):
	avalue = a.value
	bvalue = b.value

	if is_normalized_add(a, b):
		yield Add(a, b, generation)

	if avalue != 1 and bvalue != 1:
		if is_normalized_mul(a, b):
			yield Mul(a, b, generation)

	if avalue > bvalue:
		if avalue - bvalue != bvalue and is_normalized_sub(a, b):
			yield Sub(a, b, generation)

		if bvalue != 1 and (avalue % bvalue) == 0 and (avalue // bvalue) != bvalue and is_normalized_div(a, b):
			yield Div(a, b, generation)

	elif avalue == bvalue and bvalue != 1:
		if is_normalized_div(a, b):
			yield Div(a, b, generation)

def make(a, b, generation):
	avalue = a.value
	bvalue = b.value

	if is_normalized_add(a, b):
		yield Add(a, b, generation)
	elif is_normalized_add(b, a):
		yield Add(b, a, generation)

	if avalue != 1 and bvalue != 1:
		if is_normalized_mul(a, b):
			yield Mul(a, b, generation)
		elif is_normalized_mul(b, a):
			yield Mul(b, a, generation)

	if avalue > bvalue:
		if avalue - bvalue != bvalue and is_normalized_sub(a, b):
			yield Sub(a, b, generation)

		if bvalue != 1 and (avalue % bvalue) == 0 and (avalue // bvalue) != bvalue and is_normalized_div(a, b):
			yield Div(a, b, generation)
	
	elif bvalue > avalue:
		if bvalue - avalue != avalue and is_normalized_sub(b, a):
			yield Sub(b, a, generation)

		if avalue != 1 and (bvalue % avalue) == 0 and (bvalue // avalue) != avalue and is_normalized_div(b, a):
			yield Div(b, a, generation)

	elif bvalue != 1:
		if is_normalized_div(a, b):
			yield Div(a, b, generation)
		elif is_normalized_div(b, a):
			yield Div(b, a, generation)

def main(args):
	from time import time

	if len(args) < 3:
		raise ValueError("not enough arguments")
	
	target  = int(args[1],10)
	numbers = [int(arg,10) for arg in args[2:]]
	numbers.sort()

	if target < 0:
		raise ValueError("target has to be >= 0")

	if any(num <= 0 for num in numbers):
		raise ValueError("numbers have to be > 0")

	number_counts = {}
	annot_map = [0] * len(numbers)
	for i, num in enumerate(numbers):
		number_count = number_counts.get(num,0)
		annot_map[i] = number_count
		number_counts[num] =  number_count + 1

	print 'target  = %r' % target
	print 'numbers = %r' % (numbers,)

	print "solutions:"
	start = last = time()
	try:
#		for solution in solutions(target,numbers):
#			print str(solution)
		for i, solution in enumerate(solutions(target, numbers)):
			now = time()
			print "%3d [%4d / %4d secs]: %s" % (i+1, now - last, now - start, solution)
			last = now
	except KeyboardInterrupt:
		print
	print "%f seconds in total" % (time() - start)

if __name__ == '__main__':
	import sys
	main(sys.argv)
