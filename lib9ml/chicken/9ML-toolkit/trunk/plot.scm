
;;
;; Support for plotting of NineML values and data output.
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


(module 9ML-plot

	(
         plot-verbose
	 plot-ivp plot-diagram html-report 
	 )

	(import scheme chicken )


	(require-library sxml-transforms)

	(require-extension 9ML-eval)
	(require-extension object-graph signal-diagram)

        (require-library srfi-1 data-structures extras utils files)
	(import (only srfi-1 fold combine every concatenate list-tabulate)
		(only data-structures intersperse string-intersperse ->string )
		(only extras fprintf pp)
		(only utils system*)
		(only files make-pathname pathname-directory pathname-file)
		)


(define plot-verbose (make-parameter 0))

(define (d fstr . args)
  (let ([port (current-error-port)])
    (if (positive? (plot-verbose)) 
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


(define (plot-diagram prefix diagram-id tree)

  (let ((sexpr (sxml-value->sexpr tree)))
    
    (reset-graph)
    (let recur ((sexpr sexpr))
      (or (and (pair? sexpr)
               (case (car sexpr)
                 ((diagram) 
                  (let ((sexpr (cdr sexpr)))
                    
                    (case (car sexpr)
                      
                      ((RTRANSITION)  
                       (let ((f (cadr sexpr)) (fk (caddr sexpr))
                             (e (recur (cadddr sexpr))) (ek (recur (car (cddddr sexpr)))))
                         (let ((node (register-node (gensym 'rtransition)))
                               (fnode (recur f))
                               (fknode (recur fk)))
                           (set-label node "RTRANSITION")
                           (let ((edge1  (register-edge node fnode))
                                 (edge2  (register-edge node fknode)))
                             (set-label edge1 e)
                             (set-label edge2 ek)
                             node
                             ))))
                      
                      ((TRANSITION)  
                       (let ((f (cadr sexpr)) (fk (caddr sexpr))
                             (e (recur (cadddr sexpr))) )
                         (let ((node (register-node (gensym 'transition)))
                               (fnode (recur f))
                               (fknode (recur fk)))
                           (set-label node "TRANSITION")
                           (let ((edge1  (register-edge node fnode)))
                             (set-label edge1 e)
                             node
                             ))))
                      
                      ((TRANSIENT)  
                       (let ((f (cadr sexpr)) (fk (caddr sexpr))
                             (e (recur (cadddr sexpr))) )
                         (let ((node (register-node (gensym 'transient)))
                               (fnode (recur f))
                               (fknode (recur fk)))
                           (set-label node "TRANSIENT")
                           (let ((edge1  (register-edge node fnode)))
                             (set-label edge1 e)
                             node
                             ))))
                      
                      ((IDENTITY)       (let ((n1 (recur (cadr sexpr))))
                                          (let ((node (register-node (gensym 'IDENTITY))))
                                            (set-label node "IDENTITY")
                                            (let ((edge1 (register-edge node n1)))
                                              (set-label edge1 "n1")
                                              node))))

                      ((PURE)           (let ((f (sexpr->function (cadr sexpr))))
                                          (let ((node (register-node (gensym 'function))))
                                            (set-label node (sprintf "fn ~A => ~A" 
                                                                     (function-formals f) 
                                                                     (function-body f)))
                                            node)))

                      ((GROUP)          (let ((n1 (recur (cadr sexpr))) 
                                              (n2 (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'UNION))))
                                            (set-label node "UNION")
                                            (let ((edge1 (register-edge node n1))
                                                  (edge2 (register-edge node n2)))
                                              (set-label edge1 "n1")
                                              (set-label edge1 "n2")
                                              node
                                              ))))

                      ((SEQUENCE)       (let ((n1 (recur (cadr sexpr))) 
                                              (n2 (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'sequence))))
                                            (set-label node "SEQUENCE")
                                            (let ((edge1 (register-edge node n1))
                                                  (edge2 (register-edge node n2)))
                                              (set-label edge1 "n1")
                                              (set-label edge1 "n2")
                                              node
                                              ))))

                      ((UNION)          (let ((n1 (recur (cadr sexpr))) 
                                              (n2 (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'UNION))))
                                            (set-label node "UNION")
                                            (let ((edge1 (register-edge node n1))
                                                  (edge2 (register-edge node n2)))
                                              (set-label edge1 "n1")
                                              (set-label edge1 "n2")
                                              node
                                              ))))

                      ((SENSE)          (let ((sns (cadr sexpr)) (n (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'SENSE))))
                                            (set-label node (sprintf "SENSE ~A" sns))
                                            (let ((edge (register-edge node n)))
                                              node
                                              ))))
                      
                      ((ACTUATE)        (let ((sns (cadr sexpr)) (n (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'ACTUATE))))
                                            (set-label node (sprintf "ACTUATE ~A" sns))
                                            (let ((edge (register-edge node n)))
                                              node
                                              ))))

                      ((ODE)            (let ((ivar (cadr sexpr)) (dvar (caddr sexpr))
                                              (rhs (recur (cadddr sexpr))))
                                          (let ((node (register-node (gensym 'ODE))))
                                            (set-label node (sprintf "D (~A ~A) = ~A" dvar ivar rhs))
                                            node
                                            )))

                      ((ASSIGN)         (let ((var (cadr sexpr)) 
                                              (rhs (recur (caddr sexpr))))
                                          (let ((node (register-node (gensym 'ASSGIN))))
                                            (set-label node (sprintf "~A = ~A" var rhs))
                                            node
                                            )))
                      
                      (else (error 'plot-diagram "invalid diagram constructor" sexpr)))))
                 
                 ((realsig)   (let ((name (cadr sexpr))
                                    (value (caddr sexpr)))
                                name))
                 
                 ((boolsig)   (let ((name (cadr sexpr))
                                    (value (caddr sexpr)))
                                name))
                 
                 (else (map recur sexpr))
                 ))
          sexpr))
    
    (let* ((dir (pathname-directory prefix))
           (dot-path (make-pathname dir (string-append (->string diagram-id) ".dot")))
           (png-path (make-pathname dir (string-append (->string diagram-id) ".png"))))
      (with-output-to-file  dot-path
        (lambda ()
          (render-graph/dot (current-output-port))
          ))
      
      (run (dot -Tpng ,dot-path > ,png-path))
      )
    
    ))


(define (plot-ivp prefix ivp-info #!key (format 'png) (index #f))
  (let ((ivp-id (car ivp-info))
	(dvars (caddr ivp-info)))
    (let* ((n (+ 1 (length dvars)))
	   (range (if (and index (integer? index)) (number->string index) (sprintf "2:~A" n)))
	   (linewidth 3)
	   (dir (or (pathname-directory prefix) "."))
	   (log-path (make-pathname dir (sprintf "~A_~A.log" (pathname-file prefix) ivp-id)))
	   (png-path (make-pathname dir (sprintf "~A_~A.png" (pathname-file prefix) ivp-id)))
	   (eps-path (make-pathname dir (sprintf "~A_~A.eps" (pathname-file prefix) ivp-id)))
	   )
      (case format
	     ((png)
	      (run (octave -q --eval 
			   #\'
			   log = load (,(sprintf "\"~A\"" log-path)) #\; 
			   h = plot ("log(:,1)" #\, ,(sprintf "log(:,~A)" range)) #\; 
			   ,@(if index 
				 (concatenate (list-tabulate 1 (lambda (i) `(set (h(,(+ 1 i)) #\, "\"linewidth\"" #\, ,linewidth) #\;))))
				 (concatenate (list-tabulate (- n 1) (lambda (i) `(set (h(,(+ 1 i)) #\, "\"linewidth\"" #\, ,linewidth) #\;)))))
			   print (,(sprintf "\"~A\"" png-path) #\, "\"-dpng\"") #\; 
			   #\')))
	     ((eps)
	      (run (octave -q --eval 
			   #\'
			   log = load (,(sprintf "\"~A\"" log-path)) #\; 
			   h = plot ("log(:,1)" #\, ,(sprintf "log(:,~A)" range)) #\; 
			   ,@(if index 
				 (concatenate (list-tabulate 1 (lambda (i) `(set (h(,(+ 1 i)) #\, "\"linewidth\"" #\, ,linewidth) #\;))))
				 (concatenate (list-tabulate (- n 1) (lambda (i) `(set (h(,(+ 1 i)) #\, "\"linewidth\"" #\, ,linewidth) #\;)))))
			   print (,(sprintf "\"~A\"" eps-path) #\, "\"-depsc2\"") #\; 
			   #\')))
	     (else (error 'plot-ivp "unrecognized format" format)))
      )))


)
