
(define (Random:module-initialize module-name enter-module find-module eval-env)

  (define path-real   (Pident (ident-create "real")))
  (define real-type   (Tcon (Tpath path-real) '()))

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
			(make-valtype '() (arrow-type real-type real-type))))
	   '("exponential"))

	  (map 
	   (lambda (name)
	     (Value_sig (ident-create name)
			(make-valtype '() (arrow-type real-type (arrow-type real-type real-type)))))
	   '("uniform" "normal"))

	  ))

	(struct 
	 (append

	  (map (lambda (name) (datacon 'random name 2))
	       '(uniform normal)
	       )

	  (map (lambda (name) (datacon 'random name 1))
	       '(exponential)
	       )

	  ))
	)
    
    (let* ((modname (ident-create module-name))
	   (msig    (Signature sig))
	   (mdef    (Module_def modname (Structure struct))))
      (enter-module modname msig)
      (eval-env (mod-eval-cbv (eval-env) (list mdef)))
      )
    ))
  
    


