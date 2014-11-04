;;
;;  An IVP solver for NineML.
;;
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

(require-extension posix srfi-13 datatype static-modules miniML miniMLsyntax miniMLvalue miniMLeval)
(require-extension getopt-long ssax sxml-transforms sxpath sxpath-lolevel object-graph signal-diagram)
(require-extension 9ML-parse 9ML-eval 9ML-plot)
(require-extension 9ML-ivp-octave 9ML-ivp-chicken 9ML-ivp-mlton 9ML-ivp-octave-mlton )
	


(include "SXML.scm")
(include "SXML-to-XML.scm")

(define-values (env-binding? env-empty env-add-signature env-add-module env-add-type env-add-spec env-add-value
	        env-find-value env-find-type env-find-module env-find)
  (make-mod-env core-syntax))

(define-values (scope-typedecl scope-modtype scope-signature scope-modterm scope-moddef)
  (make-mod-scoping core-syntax core-scoping))

(define-values (check-modtype check-signature type-modterm type-moddef type-definition)
  (make-mod-typing core-syntax core-typing))



(include "NineMLcore.scm")
(include "NineMLreal.scm")
(include "NineMLrandom.scm")
(include "NineMLsignal.scm")
(include "NineMLdiagram.scm")
(include "NineMLinterval.scm")
(include "NineMLgraph.scm")
(include "NineMLivp.scm")


(define init-scope      (make-parameter st-empty))
(define init-type-env   (make-parameter env-empty))
(define init-eval-env   (make-parameter env-empty))


(define (enter-typedecl id decl)
  (init-scope (st-enter-type id (init-scope)))
  (init-type-env   (env-add-type id decl (init-type-env))))

(define (enter-valtype name ty)
  (let ((id (ident-create name)))
    (init-scope (st-enter-value id (init-scope)))
    (init-type-env   (env-add-value id ty (init-type-env)))))

(define (enter-val name val)
  (let ((id (or (and (ident? name) name) (ident-create name))))
    (init-eval-env (ident-add id val (init-eval-env)))))

(core-initialize enter-typedecl enter-valtype)
(eval-cbv-initialize enter-val)


(define (enter-module id mty)
  (init-scope (st-enter-module id (init-scope)))
  (init-type-env (env-add-module id mty (init-type-env))))


(define lookup-def 
  (lambda (k lst . rest)
    (let-optionals rest ((default #f))
      (alist-ref k lst eq? default))))


(define opt-defaults
  `(
    (platform . chicken)
    ))

(define (defopt x)
  (lookup-def x opt-defaults))

                 
(define opt-grammar
  `(

    (print-type-env  "prints the type environment of each operand"
		     (single-char #\t)
		     (value (optional COMPONENT-LIST)
			    (default all)
			    (transformer 
			     ,(lambda (x) 
				(if (string=? x "all") x
				    (list (string-split x ",")))))))

    (print-eval-env  "prints the evaluation environment of each operand"
		     (single-char #\e)
		     (value (optional COMPONENT-LIST)
			    (default all)
			    (transformer 
			     ,(lambda (x) 
				(if (string=? x "all") x
				    (list (string-split x ",")))))))

    (print-source-defs  "prints the source definitions of each operand"
			(single-char #\s))

    (html-report        "prints out an HTML report of the unified environments of each operand")

    (output-sxml        "sets output format to SXML")

    (output-xml         "sets output format to XML")

    (data            "save data from simulations in files ${OPERAND}_NAME.log"
		     (single-char #\d))

    (plot            "save PNG plots of simulation data in files ${OPERAND}_NAME.png"
		     (single-char #\p))

    (plot-eps        "save EPS plots of simulation data in files ${OPERAND}_NAME.eps")

    (plot-index      "specify index of variable to plot"
		     (value (required INDEX)
			    (predicate  ,(lambda (x) (integer? (string->number x))))
			    (transformer ,string->number)
			     ))

    (xml            "reads canonical NineML XML representation of each operand"
		    (single-char #\x))

    (platform        "simulation platform (one of chicken, chicken/cvode, mlton, octave, octave/mlton)"
		     (value (required PLATFORM)
			    (predicate 
			     ,(lambda (x) 
				(let ((s (string->symbol (string-downcase x))))
				  (case s
				    ((chicken chicken/cvode mlton octave octave/mlton) s)
				    (else (error 'ivp "unrecognized platform" x))))))
			    (transformer ,string->symbol)
			     ))

    (verbose          "print commands as they are executed"
		      (single-char #\v))


    (help         (single-char #\h))           

    ))


;; Process arguments and collate options and arguments into OPTIONS
;; alist, and operands (filenames) into OPERANDS.  You can handle
;; options as they are processed, or afterwards.

(define opts    (getopt-long (command-line-arguments) opt-grammar))
(define opt     (make-option-dispatch opts opt-grammar))

(define simulation-platform (make-parameter #f))
(define ivp-verbose (make-parameter 0))

(define (d fstr . args)
  (let ([port (current-error-port)])
    (if (positive? (ivp-verbose)) 
	(begin (apply fprintf port fstr args)
	       (flush-output port) ) )))

(define (run:execute explist)
  (define (smooth lst)
    (let ((slst (map ->string lst)))
      (string-intersperse (cons (car slst) (cdr slst)) " ")))
  (for-each (lambda (cmd) (system (->string cmd)))
	    (map smooth explist)))

(define (run:execute* explist)
  (define (smooth lst)
    (let ((slst (map ->string lst)))
      (string-intersperse (cons (car slst) (cdr slst)) " ")))
  (for-each (lambda (cmd) (system* "~a" cmd))
	    (map smooth explist)))

(define-syntax run
  (syntax-rules ()
    ((_ exp ...)
     (begin
       (d "running ~A ...~%" (list `exp ...))
       (run:execute* (list `exp ...))))))

(define-syntax run-
  (syntax-rules ()
    ((_ exp ...)
     (begin
       (d "running ~A ...~%" (list `exp ...))
       (run:execute (list `exp ...))))))


;; Use args:usage to generate a formatted list of options (from OPTS),
;; suitable for embedding into help text.
(define (ivp:usage)
  (print "Usage: " (car (argv)) " file1... [options...] ")
  (newline)
  (print "The following options are recognized: ")
  (newline)
  (print (parameterize ((indent 5)) (usage opt-grammar)))
  (exit 1))


(define nl "\n")



(define (generate-ivp-table prefix ivp-id sxml-tuple #!key (platform 'chicken))

  (let ((sexpr 
	 (let ((sexpr (sxml-value->sexpr sxml-tuple)))
	   (case (car sexpr)
	     ((ivp)
	      (and (pair? (cdr sexpr))
		   (case (cadr sexpr)
		     ((construct)  (cddr sexpr))
		     (else #f))))
	     (else #f)))))
      (and sexpr
	   (let* ((ivar    (cadr sexpr))
		  (hvar    (caddr sexpr))
		  (start   (cadddr sexpr))
		  (end     (cadddr (cdr sexpr)))
		  (diagram+initial (sexpr->diagram+initial hvar (car sexpr))))
	     (let ((sd       (construct (car diagram+initial)))
		   (ic       (cadr diagram+initial)))
	       (if (not (alist-ref ivar ic))
		   (error 'generate-ivp-table "IVP independent variable is not present in given system" ivar))
	       (if (not (alist-ref hvar ic))
		   (error 'generate-ivp-table "IVP step variable is not present in given system" hvar))
	       (let* ((dfe (dataflow sd '()))
		      (dvars (lset-difference eq?
					      (lset-intersection eq? (alist-ref 'in dfe) (alist-ref 'out dfe))
					      (list ivar)))
		      (pvars (lset-difference eq? (alist-ref 'in dfe) (cons ivar dvars)))
		      (events (events sd))
		      )


		 (case platform
		   
		   ((octave)
		    (process-fork
		     (lambda () (ivp-octave prefix ivp-id hvar ivar dvars pvars events start end ic sd)))
		    (list ivp-id ivar dvars) )

		   ((octave/mlton octave-mlton)
		    (process-fork
		     (lambda () (ivp-octave-mlton prefix ivp-id hvar ivar dvars pvars start end ic sd)))
		    (list ivp-id ivar dvars) )
		   
		   ((mlton)
		    (process-fork
		     (lambda () (ivp-mlton  prefix ivp-id ivar dvars pvars start end ic sd)))
		    (list ivp-id ivar dvars) )

		   ((chicken)
		    (process-fork
		     (lambda () (ivp-chicken prefix ivp-id ivar dvars pvars events start end ic sd)))
		    (list ivp-id ivar dvars) )

		   ((chicken/cvode)
		    (process-fork
		     (lambda () (ivp-chicken/cvode prefix ivp-id hvar ivar dvars pvars events start end ic sd)))
		    (list ivp-id ivar dvars) )

		   (else (error 'generate-ivp-table "unknown platform"  platform))
		   
		   )))
	     )))
  )



(define (make-ivp-data-hook #!key (ivp #f) (diagram #f))
  (lambda (prefix name label value)
    (cond
     ((and diagram
	   (or (and (string? label) (string=? label "diagram")) 
	       (and (pair? label) (string=? (car label) "diagram")))) ;; value is a diagram
      (let* ((diagram-id (gensym 'diagram))
	     (diagram-link `(img (@ (src ,(sprintf "~A.png" diagram-id))) (alt "NineML diagram"))))
	(plot-diagram prefix diagram-id value)
	diagram-link
	))
     
     ((and ivp (or (and (string? label) (string=? label "ivp"))
		   (and (pair? label) (string=? (car label) "ivp")))) ;; value is an IVP
      (let ((ivp-id (gensym (string->symbol (string-append (->string name) "ivp")))))
	(let ((ivp-info (generate-ivp-table prefix ivp-id value platform: (simulation-platform))))
	  ivp-info
	))
      )
     
     (else #f))))
	    

(define (make-ivp-plot-hook #!key (ivp #f) (plot-format 'png) (plot-index #f))
  (lambda (prefix name label value)
    (cond

     ((and ivp (or (and (string? label) (string=? label "ivp"))
		   (and (pair? label) (string=? (car label) "ivp")))) ;; value is an IVP
      (let* ((ivp-id (gensym 'ivp))
	     (ivp-plot-link `(img (@ (src ,(sprintf "~A_~A.png" (pathname-file prefix) ivp-id)) (alt "NineML IVP plot")))))

	(let ((ivp-info (generate-ivp-table prefix ivp-id value platform: (simulation-platform))))
	  (plot-ivp prefix ivp-info format: plot-format index: plot-index)
	  ivp-plot-link)
	))
     
     (else #f))))
	    



(define (parse-xml fpath)
  (with-input-from-file fpath
    (lambda () (cons '*TOP* (ssax:xml->sxml (current-input-port) `((nml . ,nineml-xmlns) (nml . "CoModL")))))
    ))


(define (interpreter operand #!key (xml #f))

  (let ((defs (if xml (parse-al-sxml (parse-xml operand))
		  (call-with-input-file operand (lambda (in) (parse 'NineML in))))))


    (let* ((scoped-defs      (scope-moddef (init-scope) defs))
	   (mty              (type-moddef (init-type-env) '() scoped-defs))
	   (type-env         (map (lambda (x) (cases modspec x
						     (Value_sig (id vty) (cons id x))
						     (Type_sig (id decl) (cons id x))
						     (Module_sig (id mty) (cons id x))
						     )) mty))
	   (eval-env         (mod-eval-cbv (init-eval-env) scoped-defs))
	   (unified-env      (list scoped-defs 
				   (filter (lambda (x) (not (assoc (car x) (init-type-env)))) type-env) 
				   (filter (lambda (x) (not (assoc (car x) (init-eval-env)))) eval-env) ))

	   )
      unified-env
      )))


(define (main options operands)

  (if (options 'help) (ivp:usage))

  (let ((find-module (lambda (x) (env-find-module x (init-type-env)))))
    (for-each (lambda (init name) (init name enter-module find-module init-eval-env))
	      (list Real:module-initialize   
		    Random:module-initialize   
		    Signal:module-initialize   
		    Diagram:module-initialize  
		    Interval:module-initialize 
		    Graph:module-initialize
		    IVP:module-initialize )
	      (list "Real" "Random" "Signal" "Diagram" "Interval" "Graph" "IVP" )) )

  (if (null? operands)
      (ivp:usage)
      (let ((output-type (cond ((options 'output-xml)  'xml)
			       ((options 'output-sxml) 'sxml)
			       (else #f)))
	    (unified-envs (map (lambda (x) (interpreter x xml: (options 'xml))) operands)))
	(if (options 'verbose) (begin (eval-verbose 1) (ivp-verbose 1)))
	(simulation-platform (or (options 'platform) (defopt 'platform) ))
	(for-each
	 (lambda (operand uenv)
	   (let ((source-defs (car uenv))
		 (mty         (cadr uenv))
		 (eval-env    (caddr uenv)))
	     
	     (let ((type-env-opt (options 'print-type-env)))
	       (if type-env-opt
		   (if (and (string? type-env-opt) (string=?  type-env-opt "all"))
		     (print-type-env mty output-type)
		     (let ((fc (lambda (x) (and (member (ident-name (car x)) type-env-opt) x))))
		       (print-type-env mty output-type fc)))
		   ))

	     (let ((eval-env-opt (options 'print-eval-env)))
	       (if eval-env-opt
		   (if (and (string? eval-env-opt) (string=? eval-env-opt "all"))
		     (print-eval-env eval-env)
		     (let ((fc (lambda (x) (and (member (ident-name (car x)) eval-env-opt) x))))
		       (print-eval-env eval-env output-type fc)))
		   ))

	     (if (options 'print-source-defs)
		 (print-source-defs source-defs output-type))

	     (if (options 'html-report)
		 (html-report operand uenv value-hook: (make-ivp-data-hook diagram: #t ivp: #t )))

	     (if (or (options 'data) (options 'plot) (options 'plot-eps))
		 (begin
		   (traverse-definitions operand uenv value-hook: (make-ivp-data-hook ivp: #t))
		   (process-wait) ))

	     (if (options 'plot)
		    (traverse-definitions operand uenv value-hook: (make-ivp-plot-hook ivp: #t plot-index: (options 'plot-index))))

	     (if (options 'plot-eps)
		 (traverse-definitions operand uenv value-hook: (make-ivp-plot-hook ivp: #t plot-format: 'eps plot-index: (options 'plot-index))))

	     ))
	 operands unified-envs))))

(width 40)
(main opt (opt '@))
