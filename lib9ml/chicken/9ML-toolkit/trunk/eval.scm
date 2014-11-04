
;;
;; Support for evaluation of NineML.
;;
;; Copyright 2010-2012 Ivan Raikov and the Okinawa Institute of
;; Science and Technology.
;;
;; This program is free software: you can redistribute it and/or
;; modify it under the terms of the GNU General Public License as
;; published by the Free Software Foundation, either version 3 of the
;; License, or (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.
;;
;; A full copy of the GPL license can be found at
;; <http://www.gnu.org/licenses/>.
;;


(module 9ML-eval

	(eval-verbose 
         print-eval-env print-type-env print-source-defs 
	 traverse-definitions definition-apply
	 sxml-value->sexpr sexpr->function sexpr->diagram+initial 
	 sigfun-eval real-eval random-eval
         print-fragments 
         html-report 
	 )

	(import scheme chicken )

	(require-library srfi-1 srfi-13 data-structures extras utils files irregex mathh)
	(import (only srfi-1 fold combine every zip unzip2 filter-map partition delete-duplicates)
		(only srfi-13 string-downcase string-concatenate)
		(only data-structures conc compose identity atom? intersperse string-intersperse ->string )
		(only extras fprintf pp)
		(only utils system*)
		(only files make-pathname pathname-directory)
		(only mathh cosh tanh log10)
		(only irregex irregex-search irregex-match-num-submatches irregex-match-start-index irregex-match-end-index)
		)

	(require-library sxml-transforms)
	(import (prefix sxml-transforms sxml:))

	(require-extension datatype sxpath sxpath-lolevel)
	(require-extension static-modules miniML miniMLvalue miniMLeval)
	(require-extension signal-diagram signal-diagram-dynamics)
	(require-extension object-graph)
	(require-extension random-mtzig)

(include "SXML.scm")
(include "SXML-to-XML.scm")


(define random-state (random-mtzig:init))

(define eval-verbose (make-parameter 0))

(define (d fstr . args)
  (let ([port (current-error-port)])
    (if (positive? (eval-verbose)) 
	(begin (apply fprintf port fstr args)
	       (flush-output port) ) )))


(define (enumvars expr ax)
  (if (pair? expr)
      (case (car expr)
	((cond)  (fold (lambda (x ax) (enumvars x ax)) ax (cdr expr)))
	(else  (if (symbol? (car expr))  (fold (lambda (x ax) (enumvars x ax)) ax (cdr expr)) ax)))
      (if (symbol? expr) (cons expr ax) ax)))


(define (sexpr->function sexpr)  (make-function (enumvars sexpr '()) sexpr))


(define (sxml-path->symbol p)
  (let recur ((p p) (ax '()))
    (case (car p)
      ((path) (recur (cadr p) ax))
      ((Pident)
       (let ((id (sxml:text (cdr p))))
	 (let ((ax1 (cons id ax)))
	   (string->symbol (string-concatenate (intersperse  ax1 ".")))
	   )))
      ((Pdot)
       (let ((name (sxml:attr p 'name)))
	 (recur (sxml:kid p) (cons (sxml:text name) ax))))
      (else (error 'sxml-path->symbol "invalid path" p))
      )))
    

    


(define (sxml-term->sexpr term)
  (let ((tree
	 (sxml:pre-post-order* 
	  term
	  `(
	    (Const 
	     (
	      (label *preorder* . ,(lambda (tag elems) (string->symbol (sxml:text elems))))
	      
	      (string *preorder* . ,(lambda (tag elems) (sxml:text elems)))
	      
	      (real *preorder* . ,(lambda (tag elems) 
				    (let ((v (sxml:text elems)))
				      (if (number? v) v (string->number v)))))
	      
	      (nat  *preorder* . ,(lambda (tag elems) 
				    (let ((v (sxml:text elems)))
				      (if (number? v) v (string->number v)))))
	      
	      (bool *preorder* . ,(lambda (tag elems) (if (string=? (sxml:text elems) "true") #t #f)))
	      
	      (null *preorder* . ,(lambda (tag elems) '()))
	      
	      (*text* . ,(lambda (trigger str) str))
	      
	      (*default* . ,(lambda (tag elems) (cons tag elems)))
	      )
	     
	     . ,(lambda (tag elems)  (car elems)))

	    (Longid *preorder* . ,(lambda (tag elems) (sxml-path->symbol (car elems))))
	    (Function *preorder* . ,(lambda (tag elems) 
				      (let ((formal (string->symbol (sxml:attr (cons tag elems) 'formal)))
					    (body (sxml:kid elems)))
					`(lambda (,formal) ,(sxml-term->sexpr body)))))
	    (Let0 *preorder* . ,(lambda (tag elems)
				  (let ((name (string->symbol (sxml:attr (cons tag elems) 'name)))
					(value (sxml:kidn-cadr 'value (cons tag elems)))
					(body (sxml:kidn-cadr 'body (cons tag elems))))
				    `(let ((,name ,(sxml-term->sexpr value)))
				       ,(sxml-term->sexpr body)))))
	    (Apply *macro* . ,(lambda (tag elems) 
				(let ((left (sxml:kidn-cadr 'left (cons tag elems)))
				      (right (sxml:kidn-cadr 'right (cons tag elems))))
				  `(,left ,right))))
	    (*text* . ,(lambda (trigger str) str))
	    (*default* . ,(lambda (tag elems) (cons tag elems)))
	    ))))
    tree))


(define (sxml-eval-env->sexpr env fin)
  (let recur ((env env) (ax '()))
    (if (null? env) 
	`(let (,ax) ,fin)
	(let ((en (car env)))
	  (let ((name (string->symbol (sxml:attr en 'name)))
		(value (sxml-value->sexpr (sxml:kid en))))
	    (let ((en (list name value)))
	      (recur (cdr env) (if value (cons en ax) ax))
	      )))
	)))

					 
(define (sxml-value->sexpr tree)
    (let* ((tree 
	    (sxml:pre-post-order* 
	    tree
	    `(
	      (Tuple *macro*  .
		      ,(lambda (tag elems) 
			 (let ((node (cons tag elems)))
			   (let ((left (sxml:kidn-cadr 'left node))
				 (right (sxml:kidn-cadr 'right node)))

			     (list left right)))
			 ))

	      (Const (
		      (label . ,(lambda (tag elems) (string->symbol (car elems))))
		      
		      (string . ,(lambda (tag elems) (car elems)))
		      
		      (real . ,(lambda (tag elems) (let ((v (car elems)))
						     (if (number? v) v (string->number v)))))
		      
		      (nat  . ,(lambda (tag elems) (let ((v (car elems)))
						     (if (number? v) v (string->number v)))))
		      
		      (bool . ,(lambda (tag elems) (if (string=? (car elems) "true") #t #f)))
		      
		      (null . ,(lambda (tag elems) '()))
		      
		      (*text* . ,(lambda (trigger str) str))

		      (*default* . ,(lambda (tag elems) (cons tag elems)))

		      ) . ,(lambda (tag elems) 
			     (car elems)))

	      (Closure .
		       ,(lambda (tag elems) 
			  (let ((node (cons tag elems)))
			    (let ((body (sxml:kidn-cadr 'body node))
				  (env  (sxml:kidn-cdr 'env node)))
			      (let ((term (sxml-term->sexpr body)))
				(list (sxml-eval-env->sexpr env term))
				;;				(list term)
				)))
			  ))

	      (null . ,(lambda (tag elems) '()))

	      (*text* . ,(lambda (trigger str) str))

	      (*default* . ,(lambda (tag elems) (cons tag elems)))

	      )))

    	   (tree
	    (sxml:pre-post-order* 
	     tree
	     `(
	       (signal . ,(lambda (tag elems) (caar elems)))
	       
	       (sigfun . ,(lambda (tag elems) (car elems)))

	       (*text* . ,(lambda (trigger str) str))

	       (*default* . ,(lambda (tag elems) (cons tag elems)))
	       )))

	   (tree
	    (let flatten ((tree tree))
	      (cond ((or (atom? tree) (null? tree) (null? (cdr tree))) tree)
		    (else (cons (flatten (car tree)) 
				(flatten (cadr tree)))))))

             )
      tree))


;; based on SRV:send-reply by Oleg Kiselyov
(define (print-fragments b)
  (let loop ((fragments b) (result #f))
    (cond
      ((null? fragments) result)
      ((not (car fragments)) (loop (cdr fragments) result))
      ((null? (car fragments)) (loop (cdr fragments) result))
      ((eq? #t (car fragments)) (loop (cdr fragments) #t))
      ((pair? (car fragments))
        (loop (cdr fragments) (loop (car fragments) result)))
      ((procedure? (car fragments))
        ((car fragments))
        (loop (cdr fragments) #t))
      (else
       (display (car fragments))
       (loop (cdr fragments) #t)))))

      
(define (print-eval-env env . rest)
  (let-optionals rest ((output-type #f)  (component-filter identity))
          (let ((env (filter-map component-filter env)))

		 (case output-type
		   ((sxml )
		    (pp (eval-env->sxml env)))


		   ((xml )
		    (let* ((doc1   `(Toplevel ,@(eval-env->sxml env)))
			   (doc2  (ensure-xmlns  doc1))
			   (doc3  (ensure-xmlver doc2)))
		      (print-fragments (generate-XML `(begin ,doc3)))))
		       
		   
		   (else 
		    (for-each
		     (lambda (x) 
		       (let ((id (car x))
			     (v  (cdr x)))
			 (pp `(,id ,v))
			 ))
		     env))
		   ))))


      
(define (print-type-env env . rest)
  (let-optionals rest ((output-type #f) (component-filter identity))
          (let ((env (filter-map component-filter env)))
	    (case output-type
	      ((sxml )
	       (pp (map (compose modspec->sxml cdr) env)))
	      
	      ((xml )
	       (let* ((doc1   `(Toplevel ,@(map (compose modspec->sxml cdr) env)))
		      (doc2  (ensure-xmlns doc1))
		      (doc3  (ensure-xmlver doc2)))
		 (print-fragments (generate-XML `(begin ,doc3)))))
	      
	      (else  (pp env))
	      
	      ))))
      
(define (print-source-defs defs . rest)
  (let-optionals rest ((output-type #f))

		 (case output-type
		   ((sxml )
		    (pp (map moddef->sxml defs)))

		   ((xml )
		    (let* ((doc1   `(Toplevel ,@(map moddef->sxml defs)))
			   (doc2  (ensure-xmlns doc1))
			   (doc3  (ensure-xmlver doc2)))
		      (print-fragments (generate-XML `(begin ,doc3)))))
		       
		   (else  (pp defs))

		   )))

(define (signal-op->mathml op)
  (case op
    ((add) 'plus)
    ((sub) 'minus)
    ((mul) 'multiply)
    ((div) 'divide)
    (else op)))


(define (function->nxml f)
  `(lambda ,(map (lambda (x) `(bvar ,x)) (function-formals f))
     ,(signal->nxml (function-body f))))


(define (signal->nxml tree)
    (let recur ((sexpr tree))
      (or (and (pair? sexpr)
	       (case (car sexpr)

		 ((signal) 
		  (let ((sexpr (cdr sexpr)))
		    
		    (case (car sexpr)
		      
		      ((signal)   
		       (let ((name (cadr sexpr)))
			 `(ci ,name)))
		      
		      ((realsig)   
		       (let ((name (cadr sexpr))
			     (value (caddr sexpr)))
			 `(ci (@ (type real)) ,name)))
		      
		      ((boolsig)   
		       (let ((name (cadr sexpr))
			     (value (caddr sexpr)))
			 `(ci (@ (type real)) ,name)))

		      ((if)
		       `(if ,(recur (cadr sexpr)) 
			    ,(recur (caddr sexpr))
			    ,(recur (cadddr sexpr))))
		      
		      ((add sub mul div gte lte gt lt)
		       (let ((name (signal-op->mathml (car sexpr))))
			 `(apply (,name) ,(recur (cadr sexpr)) 
				 ,(recur (caddr sexpr)))))
		       
		      ((neg log ln sin cos cosh tanh)
		       (let ((name (signal-op->mathml (car sexpr))))
			 `(apply (,name) ,(recur (cadr sexpr)) )))

		      (else (error 'signal->nxml "invalid signal function constructor" sexpr))

		      )))

		 (else (map recur sexpr))
		 )))

             sexpr))


(define (diagram->nxml sexpr)

    (let recur ((sexpr sexpr))
      (or (and (pair? sexpr)
	       (case (car sexpr)
		 ((diagram) 
		  (let ((sexpr (cdr sexpr)))
		    
		    (case (car sexpr)
		      
		      ((RTRANSITION)  
		       (let ((f (cadr sexpr)) (fk (caddr sexpr))
			     (e (cadddr sexpr)) (ek (car (cddddr sexpr))))
			 `(DiagramLib:Rtransition 
			   (@ (e ,e) (e ,ek) ,(recur f) ,(recur fk)))
			 ))
		      
		      ((TRANSITION)  
		       (let ((f (cadr sexpr)) (fk (caddr sexpr))
			     (e (cadddr sexpr))) 
			 `(DiagramLib:Transition 
			   (@ (e ,e) ,(recur f) ,(recur fk)))
			 ))
		      
		      ((TRANSIENT)  
		       (let ((f (cadr sexpr)) (fk (caddr sexpr))
			     (e (cadddr sexpr))) 
			 `(DiagramLib:Transient 
			   (@ (e ,e) ,(recur f) ,(recur fk)))
			 ))

		      ((IDENTITY)       
		       (let ((f (cadr sexpr)))
			 `(DiagramLib:Identity ,(recur f))))

		      ((RELATION)           
		       (let ((n (cadr sexpr)) (x (caddr sexpr))
			     (f (sexpr->function (cadddr sexpr)))
			     (d (car (cddddr sexpr))))
			 `(DiagramLib:Relation (@ (name ,n) (arg ,x))
					       ,(function->nxml f)
					       ,(recur d))))
			 
		      ((PURE)           
		       (let ((f (sexpr->function (cadr sexpr))))
			 `(DiagramLib:Function
			   ,(function->nxml f))))

		      ((GROUP)           
		       (let ((n1 (cadr sexpr)) (n2 (caddr sexpr)))
			 `(DiagramLib:Group
			   ,(recur n1) ,(recur n2))))

		      ((SEQUENCE)       
		       (let ((n1  (cadr sexpr))
			     (n2  (caddr sexpr)))
			 `(DiagramLib:Sequence ,(recur n1) ,(recur n2))
			 ))

		      ((UNION)          
		       (let ((n1 (cadr sexpr))
			     (n2 (caddr sexpr)))
			 `(DiagramLib:Regime ,(recur n1) ,(recur n2))
			 ))

		      ((SENSE)          
		       (let ((sns (cadr sexpr)) (n (caddr sexpr)))
			 `(DiagramLib:Sense ,(map (lambda (s) `(signal ,s)) sns) 
					    ,(recur n))
			 ))
						   
		      ((ACTUATE)        
		       (let ((sns (cadr sexpr)) (n (caddr sexpr)))
			 `(DiagramLib:Actuate ,(map (lambda (s) `(signal ,s)) sns) 
					      ,(recur n))))
		      
		      ((ODE)            
		       (let ((ivar (cadr sexpr)) (dvar (caddr sexpr))
			     (rhs (cadddr sexpr)))
			 `(DiagramLib:ODE `(independent_variable ,ivar)
					  `(dependent_variable ,dvar)
					   ,(recur rhs))))

		      ((ASSIGN)         
		       (let ((var (cadr sexpr)) 
			     (rhs (recur (caddr sexpr))))
			 `(DiagramLib:Assign `(variable ,var)
					     ,(recur rhs))))

		      
		      (else (error 'diagram->nxml "invalid diagram constructor" sexpr))
		      )))

		 (else (map recur sexpr))
		 ))

             sexpr)))


(define (print-nxml prefix uenv)

    (let (
	  (path-ss
	   `(
	     (path
	      *macro*
	      . ,(lambda (tag elems) elems))
	     
	    (Pident
	     *macro*
	     . ,(lambda (tag elems)
		  (let ((node (cons tag elems)))
		    (let ((name (sxml:text node)))
		      (if (not name) (error 'print-nxml "Pident element requires text content" node))
		      name))))
	     
	     (Pdot
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'print-nxml "Pdot element requires name attribute"))
		       `(,(sxml:kids node) "." ,name)))))

	     
	     ,@sxml:alist-conv-rules*
	     ))


	  (moddef-ss
	   
	   `(
	     (Type_def
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name))
			   (deftype (sxml:kidn* 'deftype node)))
		       `(Type (@ (name ,name)) ,deftype)))
		   ))

	     (Component
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		       (let ((name (sxml:attr node 'name))
			     (members ((sxpath '(Component (*or* Val Component))) `(*TOP* ,node))))
			 `(Namespace (@ (name ,name)) . ,members)
			 ))
		   ))

	     (Val
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let* ((name (sxml:attr node 'name))
			    (value (sxml:kid node))
			    (tuple-label ((sxpath '(Tuple left Const label *text*)) `(*TOP* ,value))))

		       (if (not name) (error 'type-env-report "binding element requires name attribute"))

		       (cond ((and (pair? tuple-label) (equal? (car tuple-label) "diagram")) ;; value is a diagram
			      (let* ((diagram-id (gensym 'diagram)))
				`(Binding (@ (name ,name)) ,(diagram->nxml (sxml-value->sexpr value)))))

			     (else
			      `(Binding (@ (name ,name))  ,value)))
		       ))))
	     
	  ,@sxml:alist-conv-rules*

	  ))


	  (term-ss
	   `(

	     (Longid 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (sxml:kids node)
		     )))

	     (Function
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((formal (sxml:attr node 'formal))
			   (body   (sxml:kid node)))
		       `(Term:Function (@ (x ,formal)) ,body)
		       ))))


	     (Let0 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name))
			   (value (sxml:kidn-cadr 'value node))
			   (body (sxml:kidn-cadr 'body node)))
		       `(Term:Let (@ (name ,name)) (value ,value) (body ,body))
		       ))))

	     (Apply 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((left (sxml:kidn-cdr 'left node))
			   (right (sxml:kidn-cdr 'right node)))
		       `(Term:Apply (left ,left) (right ,right))
		       ))))
	     
	     ,@sxml:alist-conv-rules*
	     ))


	  )

  (let (  
	(filename    (string-append prefix ".xml"))
	(source-defs (car uenv))
	(type-env    (cadr uenv))
	(eval-env    (caddr uenv)))

    (let ((eval-env-sxml (eval-env->sxml eval-env))
	  (eval-env-rulesets `(,moddef-ss
			       ,term-ss
			       ,path-ss
			       )))
      
      (let* (
	     (eval-env-sxml  (sxml-transform eval-env-sxml eval-env-rulesets))
	     (content        `(Toplevel ,eval-env-sxml))
	     )
	
	(with-output-to-file filename
	  (lambda () (print-fragments (generate-XML content))))
	    
	)))
  ))


(define (realsig-value x)
  (cond ((number? x) x)
	((equal? 'realsig (car x)) (caddr x))
	(else (error 'realsig-value "invalid real signal" x))))

(define (realsig-name x)
  (if (and (pair? x) (equal? 'realsig (car x))) (cadr x)
      (error 'realsig-name "invalid real signal" x)))

(define (boolsig-value x)
  (cond ((boolean? x) x)
	((equal? 'boolsig (car x)) (caddr x))
	(else (error 'boolsig-value "invalid boolean signal" x))))

(define (boolsig-name x)
  (if (and (pair? x) (equal? 'boolsig (car x))) (cadr x)
      (error 'boolsig-value "invalid boolean signal" x)))



(define (sigfun-eval sexpr)
  (let recur ((sexpr sexpr))
    (if (pair? sexpr)
	(case (car sexpr)
	  ((realconst)   (let ((value (cadr sexpr))) (real-eval value)))
	  ((boolconst)   (let ((value (cadr sexpr))) value))
	  ((realsig)     (let ((name (cadr sexpr))
			       (value (recur (caddr sexpr))))
			   (if (not (number? value)) (error 'realsig "real signal value is not a real" name value))
			   `(realsig ,name ,value)))
	  ((boolsig)   (let ((name (cadr sexpr))
			     (value0 (recur (caddr sexpr))))
			 (let ((value (if (boolean? value0) value0
					  (else (error 'boolsig "boolean signal value is not a boolean" name value0)))))
			   `(boolsig ,name ,value))))
	  ((neg)       (let ((x (recur (cadr sexpr))))
			 (- (realsig-value x))))
	  ((log)       (let ((x (recur (cadr sexpr))))
			 (log10 (realsig-value x))))
	  ((ln)        (let ((x (recur (cadr sexpr))))
			 (log (realsig-value x))))
	  ((cosh)      (let ((x (recur (cadr sexpr))))
			 (cosh (realsig-value x))))
	  ((tanh)      (let ((x (recur (cadr sexpr))))
			     (tanh (realsig-value x))))
	  ((+)       (let ((x (recur (cadr sexpr)))
			   (y (recur (caddr sexpr))))
		       (+ (realsig-value x) (realsig-value y))))
	  ((-)       (let ((x (recur (cadr sexpr))) 
			   (y (recur (caddr sexpr))))
		       (- (realsig-value x) (realsig-value y))))
	  ((*)       (let ((x (recur (cadr sexpr)))  
			   (y (recur (caddr sexpr))))
		       (* (realsig-value x) (realsig-value y))))
	  ((/)       (let ((x (recur (cadr sexpr)))  
			   (y (recur (caddr sexpr))))
		       (/ (realsig-value x) (realsig-value y))))
	  ((>=)       (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(>= (realsig-value x) (realsig-value y))))
	  ((<=)       (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(<= (realsig-value x) (realsig-value y))))
	  ((>)        (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(> (realsig-value x) (realsig-value y))))
	  ((<)        (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(< (realsig-value x) (realsig-value y))))
	  (else (map recur sexpr))
	  ) 
	sexpr)))



(define (real-eval sexpr)
  (let recur ((sexpr sexpr))
    (if (number? sexpr) sexpr
	(case (car sexpr)
	  ((real)      (recur (cdr sexpr)))
	  ((random)    (random-eval (cdr sexpr)))
	  ((neg)       (let ((x (recur (cadr sexpr))))
			 (- (real-eval x))))
	  ((log)       (let ((x (recur (cadr sexpr))))
			 (log10 (real-eval x))))
	  ((ln)        (let ((x (recur (cadr sexpr))))
			 (log (real-eval x))))
	  ((cosh)      (let ((x (recur (cadr sexpr))))
			 (cosh (real-eval x))))
	  ((tanh)      (let ((x (recur (cadr sexpr))))
			 (tanh (real-eval x))))
	  ((+)       (let ((x (recur (cadr sexpr)))
			   (y (recur (caddr sexpr))))
		       (+ (real-eval x) (real-eval y))))
	  ((-)       (let ((x (recur (cadr sexpr))) 
			   (y (recur (caddr sexpr))))
			   (- (real-eval x) (real-eval y))))
	  ((*)       (let ((x (recur (cadr sexpr)))  
			   (y (recur (caddr sexpr))))
			   (* (real-eval x) (real-eval y))))
	  ((/)       (let ((x (recur (cadr sexpr)))  
			       (y (recur (caddr sexpr))))
		       (/ (real-eval x) (real-eval y))))
	  ((>=)       (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(>= (real-eval x) (real-eval y))))
	  ((<=)       (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(<= (real-eval x) (real-eval y))))
	  ((>)        (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(> (real-eval x) (real-eval y))))
	  ((<)        (let ((x (recur (cadr sexpr)))  
			    (y (recur (caddr sexpr))))
			(< (real-eval x) (real-eval y))))
	  ((toNat)    (let ((v (recur (cadr sexpr))))
			(inexact->exact (abs (round v)))))
	  (else (map recur sexpr))
	  ))
    ))


(define (random-eval sexpr)
  (let recur ((sexpr sexpr))
    (if (number? sexpr) sexpr
	(case (car sexpr)

	  ((random)      
	   (recur (cdr sexpr)))

	  ((uniform)     
	   (let ((low   (real-eval (cadr sexpr)))
		 (high  (real-eval (caddr sexpr))))
	     (let ((rlo (if (< low high) low high))
		   (rhi (if (< low high) high low))) 
	       (let ((delta (+ 1 (- rhi rlo)))
		     (v (random-mtzig:randu! random-state)))
		 (+ rlo (floor (* delta v)))
		 ))
	     ))

	  ((normal)     
	   (let ((mean   (real-eval (cadr sexpr)))
		 (stddev (sqrt (real-eval (caddr sexpr)))))
	     (let ((v (random-mtzig:randn! random-state)))
	       (+ (* v stddev) mean))))

	  ((exponential) 
	   (let ((mean   (real-eval (cadr sexpr))))
	     (let ((v (random-mtzig:rande! random-state)))
	       (* v mean))))

	  (else (error 'random-eval "unknown random constructor" sexpr))
	  ))
    ))


(define (sexpr->diagram+initial h sexpr)

    (define initenv  (make-parameter '()))

    (let ((diagram
	   (let recur ((sexpr sexpr))
	     (if (pair? sexpr)
		 (case (car sexpr)
		   
		   ((diagram) 
		    (let ((sexpr (cdr sexpr)))
		      (case (car sexpr)
			
			((PURE)           (let ((f  (sexpr->function (cadr sexpr))))  (PURE f)))
			((GROUP)          (UNION (recur (cadr sexpr)) (recur (caddr sexpr))))
			((IDENTITY)       (IDENTITY (recur (cadr sexpr))))
			((SEQUENCE)       (SEQUENCE (recur (cadr sexpr)) (recur (caddr sexpr))))
			((UNION)          (UNION (recur (cadr sexpr)) (recur (caddr sexpr))))
			((SENSE)          (SENSE (cadr sexpr) (recur (caddr sexpr))))
			((ACTUATE)        (ACTUATE (cadr sexpr) (recur (caddr sexpr))))
			((TRANSIENT)      (TRANSIENT (recur (cadr sexpr)) (recur (caddr sexpr))
						     (recur (cadddr sexpr))))
			((TRANSITION)     (TRANSITION (recur (cadr sexpr)) (recur (caddr sexpr))
						      (recur (cadddr sexpr))))
			((RTRANSITION)    (RTRANSITION (recur (cadr sexpr)) (recur (caddr sexpr))
						       (recur (cadddr sexpr))
						       (recur (cadddr (cdr sexpr)))))
			
			((ODE)            (let ((deps  (map recur (cadr sexpr)))
						(indep (recur (caddr sexpr)))
						(tstep (recur (cadddr sexpr)))
						(rhs   (cadddr (cdr sexpr))))
					    
					    (if (not (equal? tstep h))
						(error 'sexpr->diagram "mismatch between independent variable step of ODE and IVP" h tstep))
					    
					    (let-values (((rhs-list relation-list)
							  (let rhs-recur ((rhs-list '()) (relation-list '()) (rhs rhs))
							    (case (car rhs)
							      ((pure)
							       (let ((d (cdr rhs)))
								 (case (car d)
								   ((GROUP)  
								    (let-values (((rhs-list1 relation-list1) 
										  (rhs-recur rhs-list relation-list (cadr d))))
								      (rhs-recur rhs-list1 relation-list1 (caddr d))))
								   ((PURE)      
								    (let ((expr (recur (cadr d))))
								      (values (cons expr rhs-list) relation-list)))
								   ((RELATION)  
								    (let ((r (cdr d)))
								      (rhs-recur rhs-list 
										 (cons (list (car r) (list (cadr r)) (recur (caddr r))) 
										       relation-list) 
										 (cadddr r))))
								   (else (error 'sexpr->diagram "invalid ODE subelement" d)))))
							      (else
							       (error 'sexpr->diagram "invalid ODE subelement" rhs))))))
					      (make-dae-system h indep (append (reverse relation-list) (zip deps (reverse rhs-list))))
					      )))
			
			((ASSIGN)         (let ((vars  (cadr sexpr))
						(rhs   (caddr sexpr)))
					    (let ((rhs-list
						   (let rhs-recur ((rhs-list '()) (rhs rhs))
						     (case (car rhs)
						       ((pure)
							(let ((d (cdr rhs)))
							  (case (car d)
							    ((GROUP)  (rhs-recur (rhs-recur rhs-list  (cadr d)) (caddr d)))
							    ((PURE)   (cons (recur (cadr d)) rhs-list))
							    (else (error 'sexpr->diagram "invalid ASSIGN subelement" d)))))
						       (else (error 'sexpr->diagram "invalid ASSIGN subelement" rhs))))))
					      
					      (make-assign-system (zip vars (reverse rhs-list))))))
			
			((RELATION)      (let ((n (cadr sexpr)) (x (caddr sexpr))
					       (f (sexpr->function (recur (cadddr sexpr)))))
					   (RELATION (list n x f) (recur (cadddr (cdr sexpr))))))
			
			(else             (error 'sexpr->diagram "invalid diagram constructor" sexpr))
			)))
		   
		   ((relation)    (let ((op (cadr sexpr))) (cons op (map recur (cddr sexpr)))))
		   
		   ((realsig)     (let ((name (cadr sexpr))
					(value (sigfun-eval (caddr sexpr))))
				    (if (not (number? value)) (error 'realsig "real signal value is not a real" name value))
				    (initenv (cons (cons name value) (initenv)))
				    name))

		   ((realconst)   (real-eval (cadr sexpr)))
		   
		   ((boolsig)   (let ((name (cadr sexpr))
				      (value0 (sigfun-eval (caddr sexpr))))
				  (let ((value (if (boolean? value0) value0
						   (case (car value0) 
						     ((boolconst) (cadr value0))
						     (else (error 'boolsig "boolean signal value is not a boolean" name value0))))))
				    (initenv (cons (cons name value) (initenv)))
				    name)))

		   ((boolconst)   (if (cadr sexpr) 'true 'false))
		   
		   (else (map recur sexpr)))
		 sexpr)
	  )))
    (initenv (delete-duplicates (initenv) (lambda (x y) (equal? (car x) (car y)))))
    (list diagram (initenv))))

    
  

(define variable-names (make-parameter '()))


(define (html-report prefix uenv #!key (value-hook #f))

  (let-syntax 
      (
       (line (syntax-rules ()
	       ((_ x ...) (list (list 'span '(@ (class "hl_line")) `x ...) nl))))
       (code (syntax-rules ()
	       ((_ x ...) (list 'code '(@ (class "hl_code")) `x ...))))
       )

    (let (
	  (path-ss
	   `(
	     (path
	      *macro*
	      . ,(lambda (tag elems) elems))
	     
	    (Pident
	     *macro*
	     . ,(lambda (tag elems)
		  (let ((node (cons tag elems)))
		    (let ((name (sxml:text node)))
		      (if (not name) (error 'html-report "Pident element requires text content" node))
		      name))))
	     
	     (Pdot
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'html-report "Pdot element requires name attribute"))
		       `(,(sxml:kids node) "." ,name)))))

	     
	     ,@sxml:alist-conv-rules*
	     ))

	  (simple-type-ss
	   `(
	     (Tcon
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((path (sxml:kidn-cadr 'path node))
			   (ts (map cdr (sxml:kidsn 't node))))
		       (cond 
			((equal? path `(pident (@ (name "->"))))
			 `(,(car ts) " -> " ,(cadr ts)))
			((pair? ts)
			 `("(" ,@(intersperse ts " ") ") " ,path))
			(else path))))))
	     
	     
	     (Tvar
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((repres (sxml:kidn 'repres node)))
		       (cond 
			(repres (cdr repres))
			(else (let* ((name (or (assq elems (variable-names))))
				     (name (if (not name)
					       (let* ((n  (+ 1 (length (variable-names))))
						     (s  (string-append "'t" (number->string n))))
						 (variable-names (cons (list n s) (variable-names)))
						 s))))
				name)))))))
	     
	     ,@sxml:alist-conv-rules*
	     ))

	  (const-ss
	   `(

	     (Const
	      *macro*
	      . ,(lambda (tag elems) 
		   (let ((node (cons tag elems)))
		     (sxml:kids node))))

	     (label 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (code ,(sxml:text node)))))
		   
	     ,@sxml:alist-conv-rules*
	     ))
	    
	  (typedef-ss
	   `(
	     (Valtype
	      *macro* 
	      . ,(lambda (tag elems)
		   (let ((body (sxml:kidn-cdr 'body elems)))
		     body)
		   ))

	     (Deftype 
	       *macro*
	       . ,(lambda (tag elems)
		    (let ((node (cons tag elems)))
		      (let ((b (sxml:kidn-cdr 'body node)))
			b)
		      )))

	     ,@sxml:alist-conv-rules*

	     ))
	  
	  (modspec-ss
	   `(
	     (Value_sig 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'type-env-report "value_sig element requires name attribute"))
		       (line "Value " (b ,name) " : " ,(sxml:kids node))))))
	     
	     
	     (Type_sig 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'type-env-report "type_sig element requires name attribute"))
		       (line "Type " (b ,name) " = " ,(sxml:kids node))))))
	     
	     (Typedecl
	      *macro* 
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((m (sxml:kidn* 'manifest node)))
		       m)
		     )))
	     
	     (manifest 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((dt (sxml:kidn* 'deftype node)))
		       dt)
		     )))
	     
	     (Module_sig 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'type-env-report "module_sig element requires name attribute"))
		       `(,(line "Component signature " (b ,name) " : ") 
			 ,(sxml:kids node))))))
	     
	     (Signature
	      *macro* 
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     `(ul . ,(map (lambda (x) `(li ,x)) (sxml:kids node ))))))
	     
	     
	     (Functorty
	      *macro* 
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'type-env-report "functorty elements requires name attribute"))
		       `("Functor " (b ,name)
			 (ul . ,(map (lambda (x) `(li ,x)) (sxml:kids node ))))))))
	     
	     
	     ,@sxml:alist-conv-rules*
	     ))

	  (moddef-ss
	   
	   `(
	     (Type_def
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name))
			   (deftype (sxml:kidn* 'deftype node)))
		       (code  "type " ,name " = " ,deftype)
		   ))))

	     (Component
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name)))
		       (if (not name) (error 'type-env-report "component element requires name attribute"))
		       `(,(line "Component " (b ,name) " = ") (ul . ,(map (lambda (x) `(li ,x)) (sxml:kids node))))))))

	     (Val
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let* ((name (sxml:attr node 'name))
			    (value (sxml:kid node))
			    (tuple-label ((sxpath '(Tuple left Const label *text*)) `(*TOP* ,value))))

		       (if (not name) (error 'type-env-report "binding element requires name attribute"))

		       (cond ((and value-hook (pair? tuple-label) (value-hook prefix name (car tuple-label) value)) =>
			      (lambda (x) `(,(line "binding " (b ,name) " = ") (p ,x))))

			     (else
			      `(,(line "binding " (b ,name) " = ") ,value)))
		       ))))

	     (Prim
	      *macro*
	      . ,(lambda (tag elems) 
		  (code "primitive procedure")))
	     
	     (null
	      *macro*
	      . ,(lambda (tag elems) 
		  (code "null")))
	     
	     (Tuple
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((left (sxml:kidn-cadr 'left node))
			   (right (sxml:kidn-cdr 'right node)))
		        `( " ( "  ,left " " ,@right " ) " )
			))))
	     
	     (Closure
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((body (sxml:kidn-cdr 'body node))
			   (env (sxml:kidn-cdr 'env node)))
		       `(,(line "Closure: ") ,@body ,(line "where ") ,env)))))

	     
	     
	  ,@sxml:alist-conv-rules*

	  ))


	  (term-ss
	   `(

	     (Longid 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (sxml:kids node))))

	     (Function
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((formal (sxml:attr node 'formal)))
		       (let-values (((formals body)
				     (let recur ((formals (list formal)) 
						 (body (sxml:kid node)))
				       (case (car body) 
					 ((function)
					  (recur 
					   (cons (sxml:attr body 'formal) formals)
					   (sxml:kid body)))
					 (else (values (reverse formals) body))))))
			 `(,(line (code "Function " ,(intersperse formals " ") " => ")) 
			   ,body))
		       ))))


	     (Let0 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((name (sxml:attr node 'name))
			   (value (sxml:kidn-cadr 'value node))
			   (body (sxml:kidn-cadr 'body node)))
		       `(,(line (code "binding " (b ,name) " = ") ,value)
			 ,body)))))
	     
	     (Apply 
	      *macro*
	      . ,(lambda (tag elems)
		   (let ((node (cons tag elems)))
		     (let ((left (sxml:kidn-cdr 'left node))
			   (right (sxml:kidn-cdr 'right node)))
		       (code ,left " (" ,right ") ")))))
	     
	     ,@sxml:alist-conv-rules*
	     ))


	  )

  (let ((filename (string-append prefix ".html"))
	(source-defs (car uenv))
	(type-env    (cadr uenv))
	(eval-env    (caddr uenv)))


    (let ((type-env-sxml (map (compose modspec->sxml cdr) type-env))
	  (eval-env-sxml (eval-env->sxml eval-env))
	  (type-env-rulesets `(,modspec-ss
			       ,typedef-ss
			       ,simple-type-ss
			       ,path-ss
			       ))
	  (eval-env-rulesets `(,moddef-ss
			       ,modspec-ss
			       ,typedef-ss
			       ,term-ss
			       ,const-ss
			       ,simple-type-ss
			       ,path-ss
			       )))
      
      (with-output-to-file filename
	(lambda ()
	  (let* ((type-env-shtml (sxml-transform type-env-sxml type-env-rulesets))
		 (eval-env-shtml (sxml-transform eval-env-sxml eval-env-rulesets))
		 (content        `(html:begin ,prefix (body (section* 1 ,prefix)
							    (toc)
							    (section 2 "Type environment") 
							    ,type-env-shtml 
							    (section 2 "Value environment")
							    ,eval-env-shtml
							    )))
		 (internal-link
		  (lambda (r)
		    (sxml:post-order 
		     r
		     `(
		       (*default* . ,(lambda (tag elems) (cons tag elems)))
		       
		       (*text* . ,(lambda (trigger str) 
				    (string-substitute* (string-downcase str) 
							'(("[^A-Za-z0-9_ \t-]" . "")
							 ("[ \t]+" . "-"))))))
		     )))
		 )

	    (print-fragments
	     (generate-XML content
			   rulesets:
			   `(((html:begin . ,(lambda (tag elems)
					       (let ((title (car elems))
						     (elems (cdr elems)))
						 (list "<HTML><HEAD><TITLE>" title "</TITLE></HEAD>"
						       "<meta http-equiv=\"Content-Style-Type\" content=\"text/css\" />"
						       "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />"

						       "<link rel=\"stylesheet\" type=\"text/css\" href=\"highlight.css\" />"
						       elems
						       "</HTML>"))))
			      (section
			       *macro*
			       . ,(lambda (tag elems)
				    (let ((level (car elems))
					  (head-word (cadr elems))
					  (contents (cddr elems)))
				      (cond ((and (integer? level) head-word)
					     `((,(string->symbol (string-append "h" (number->string level)))
						(@ (id ,(internal-link head-word)))
						,head-word ) . ,contents))
					    (else
					     (error 'html-transformation-rules
						    (conc "section elements must be of the form (section level head-word . contents), got " elems))))
					   )))

			      (section*
			       *macro*
			       . ,(lambda (tag elems)
				    (let ((level (car elems))
					  (head-word (cadr elems))
					  (contents (cddr elems)))
				      (cond ((and (integer? level) head-word)
					     `((,(string->symbol (string-append "h" (number->string level)))
						,head-word ) . ,contents))
					    (else
					     (error 'html-transformation-rules
						    (conc "section elements must be of the form (section level head-word . contents), got " elems))))
				      )))


			      (toc ;; Re-scan the content for "section" tags and generate
			       *macro*
			       . ,(lambda (tag rest) ;; the table of contents
				    `(div (@ (id "toc"))
					  ,rest
					  (ol ,(let find-sections ((content content))
						 (cond
						  ((not (pair? content)) '())
						  ((pair? (car content))
						   (append (find-sections (car content))
							   (find-sections (cdr content))))
						  ((eq? (car content) 'section)
						   (let* ((level (cadr content))
							  (head-word (caddr content))
							  (href (conc "#" (internal-link head-word)))
							  (subsections (find-sections (cdddr content))))
						     (cond ((and (integer? level) head-word)
							    `((li (a (@ (href ,href)) ,head-word)
								  ,@(if (null? subsections)
									'()
									`((ol ,subsections))))))
							   (else
							    (error 'html-transformation-rules
								   "section elements must be of the form (section level head-word . contents)")))))
						  (else (find-sections (cdr content)))))))))


			      ,@sxml:alist-conv-rules*
			      ))
			   protect: #t
			   ))
	    
	    )))

	  ;;eval-env-sxml
      )))))



(define (traverse-definitions prefix uenv #!key (type-hook #f) (component-hook #f) (value-hook #f) (filter (lambda (x) x)))

  
  (let ((source-defs (car uenv))
	(type-env    (cadr uenv))
	(eval-env    (caddr uenv)))
    
    (let recur ((eval-env eval-env))
      (if (pair? eval-env)
	  (let ((entry (car eval-env)))
	    (if (filter entry)
		(let ((v (cdr entry))
		      (name (ident-name (car entry))))
		  (cond ((MLvalue? v) 
			 (let ((sxml-value (MLvalue->sxml v)))
			   (let* ((value (sxml:kid* sxml-value))
				  (tuple-label (and value ((sxpath '(Tuple left Const label *text*)) `(*TOP* ,sxml-value)))))
			     (if (pair? tuple-label)
				 (value-hook prefix name (car tuple-label) sxml-value)))))
			(else
			 (if (modval? v)
			     (cases modval v
				    (Structure_v (env) (recur env))))))))
	    (recur (cdr eval-env))
	    ))
      ))
  )


(define (definition-apply prefix name uenv #!key (type-hook #f) (component-hook #f) (value-hook #f))

  (let ((name (if (or (string? name) (symbol? name)) (ident-create (->string name)) name))
	(source-defs (car uenv))
	(type-env    (cadr uenv))
	(eval-env    (caddr uenv)))

    (let ((v (ident-find name eval-env)))

      (and v
	     
	     (cond ((MLvalue? v) 
		    (let ((sxml-value (MLvalue->sxml v)))
		      (let* ((value (sxml:kid* sxml-value))
			     (tuple-label (and value ((sxpath '(Tuple left Const label *text*)) `(*TOP* ,sxml-value)))))
			(if (pair? tuple-label)
			    (value-hook prefix (ident-name name) (car tuple-label) sxml-value)))))
		   (else #f))
	     ))
      ))



;; Taken from regex.scm:

;;; Substitute matching strings:

(define (string-search-positions rx str #!optional (start 0) (range (string-length str)))
  (let ((n (string-length str)))
    (and-let* ((m (irregex-search rx str start (min n (fx+ start range)))))
      (let loop ((i (irregex-match-num-submatches m))
		 (res '()))
	(if (fx< i 0)
	    res
	    (loop (fx- i 1) (cons (list (irregex-match-start-index m i)
					(irregex-match-end-index m i))
				  res)))))))

(define string-substitute
  (let ([substring substring]
        [reverse reverse]
        [make-string make-string]
        [string-search-positions string-search-positions] )
    (lambda (rx subst string . flag)
      (##sys#check-string subst 'string-substitute)
      (##sys#check-string string 'string-substitute)
      (let* ([which (if (pair? flag) (car flag) 1)]
             [substlen (##sys#size subst)]
             (strlen (##sys#size string))
             [substlen-1 (fx- substlen 1)]
             [result '()]
             [total 0] )
        (define (push x)
          (set! result (cons x result))
          (set! total (fx+ total (##sys#size x))) )
        (define (substitute matches)
          (let loop ([start 0] [index 0])


                 (if (fx>= index substlen-1)
                (push (if (fx= start 0) subst (substring subst start substlen)))
                (let ([c (##core#inline "C_subchar" subst index)]
                      [index+1 (fx+ index 1)] )
                  (if (char=? c #\\)
                      (let ([c2 (##core#inline "C_subchar" subst index+1)])
                        (if (and (not (char=? #\\ c2)) (char-numeric? c2))
                            (let ([mi (list-ref matches (fx- (char->integer c2) 48))])
                              (push (substring subst start index))
                              (push (substring string (car mi) (cadr mi)))
                              (loop (fx+ index 2) index+1) )
                            (loop start (fx+ index+1 1)) ) )
                      (loop start index+1) ) ) ) ) )
        (let loop ([index 0] [count 1])
          (let ((matches (and (fx< index strlen) 
                              (string-search-positions rx string index))))
            (cond [matches
                   (let* ([range (car matches)]
                          [upto (cadr range)] )
                     (cond ((fx= 0 (fx- (cadr range) (car range)))
                            (##sys#error
                             'string-substitute "empty substitution match"
                             rx) )
                           ((or (not (fixnum? which)) (fx= count which))
                            (push (substring string index (car range)))
                            (substitute matches)
                            (loop upto #f) )
                           (else
                            (push (substring string index upto))
                            (loop upto (fx+ count 1)) ) ) ) ]
                  [else
                   (push (substring string index (##sys#size string)))
                   (##sys#fragments->string total (reverse result)) ] ) ) ) ) ) ) )

(define string-substitute*
  (let ([string-substitute string-substitute])
    (lambda (str smap . mode)
      (##sys#check-string str 'string-substitute*)
      (##sys#check-list smap 'string-substitute*)
      (let ((mode (and (pair? mode) (car mode))))
        (let loop ((str str) (smap smap))
          (if (null? smap)
              str
              (let ((sm (car smap)))
                (loop (string-substitute (car sm) (cdr sm) str mode)
                      (cdr smap) ) ) ) ) ) ) ) )



)
