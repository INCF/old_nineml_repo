(include "mathh-constants.scm")

(define (Real:module-initialize module-name enter-module find-module eval-env)

  (define path-nat   (Pident (ident-create "nat")))
  (define nat-type   (Tcon (Tpath path-nat) '()))

  (define path-real   (Pident (ident-create "real")))
  (define real-type   (Tcon (Tpath path-real) '()))

  (define path-bool   (Pident (ident-create "bool")))
  (define bool-type   (Tcon (Tpath path-bool) '()))

  (define-values (type-variables reset-type-variables
				 find-type-variable 
				 begin-def end-def newvar generalize
				 make-deftype make-valtype make-kind
				 binop ternop path-star path-list path-arrow
				 star-type list-type arrow-type label-type string-type bot-type
				 )
    (core-utils))

  (let (
	(sig
	 (append

	  (map 
	   (lambda (name)
	     (Value_sig (ident-create name)
			(make-valtype '() real-type)))
	   '("PI"))

	  (map 
	   (lambda (name)
	     (Value_sig (ident-create name)
			(make-valtype '() (arrow-type real-type (arrow-type real-type real-type)))))
	   '("add" "sub" "mul" "div"))

	  (map 
	   (lambda (name)
	     (Value_sig (ident-create name)
			(make-valtype '() (arrow-type real-type (arrow-type real-type bool-type)))))
	   '("gte" "lte" "gt" "lt" ))

	  (map 
	   (lambda (name)
	     (Value_sig (ident-create name)
			(make-valtype '() (arrow-type real-type real-type))))
	   '("neg" "log" "ln" "sin" "cos" "cosh" "tanh" ))

	  (list (Value_sig (ident-create "toNat")
			   (make-valtype '() (arrow-type real-type nat-type))))

	  ))

	(struct 
	 (append

	  (map (lambda (x v) (Value_def (ident-create (->string x))
					(Const `(real ,v))))
	       '(PI) `(,PI))

	  (map (lambda (name op) (datacon 'real name 2 op))
	       '(add sub mul div gte lte gt lt)
	       '(+ - * / >= <= > <))

	  (map (lambda (name) (datacon 'real name 1))
	       '(log ln sin cos tanh cosh neg toNat))
	  
	  ))
	)
    
    (let* ((modname (ident-create module-name))
	   (msig    (Signature sig))
	   (mdef    (Module_def modname (Structure struct))))
      (enter-module modname msig)
      (eval-env (mod-eval-cbv (eval-env) (list mdef)))
      )
    ))
  
    


