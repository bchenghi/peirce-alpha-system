:- table notEmpty//1, sentence//1, equivalence//1, conjunction//1, disjunction//1.
sentence("") --> [].
sentence(X) --> notEmpty0(X).

notEmpty0(X) --> notEmpty1(X).
notEmpty0(X) --> equivalence(X).
equivalence(and(neg(and(X, neg(Y))), neg(and(Y,neg(X))))) --> notEmpty0(X), [<,-,>], notEmpty0(Y).

notEmpty1(X) --> notEmpty2(X).
notEmpty1(X) --> implication(X).
implication(neg(and(X, neg(Y)))) --> notEmpty2(X), [-,>], notEmpty1(Y).

notEmpty2(X) --> notEmpty3(X).
notEmpty2(X) --> conjunction(X).
notEmpty2(X) --> disjunction(X).
conjunction(and(X,Y)) --> notEmpty2(X), [/,\], notEmpty3(Y). 
disjunction(neg(and(neg(X),neg(Y)))) --> notEmpty2(X), [\,/], notEmpty3(Y).

notEmpty3(X) --> notEmpty4(X).
notEmpty3(X) --> negation(X).
negation(neg(X)) --> [~], notEmpty3(X).

notEmpty4(X) --> atom(X).
notEmpty4(X) --> ['('],sentence(X), [')'], {X \= ""}.
atom(X) --> [X], {\+compound(X),is_alpha(X)}.
atom(true) --> [t,r,u,e].
atom(false) --> [f,a,l,s,e].

input(I, O) :- string_chars(I, ListOfChars), delete(ListOfChars, ' ', Output), sentence(O, Output, []).
split(I, O, O1) :- term_to_atom(C, I), C =.. [_, O, O1].
