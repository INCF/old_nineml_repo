; *** This file starts with a copy of the file multilex.scm ***
; Copyright (C) 1997 Danny Dube', Universite' de Montre'al.
; All rights reserved.
; SILex 1.0.

;
; Gestion des Input Systems
; Fonctions a utiliser par l'usager:
;   lexer-make-IS, lexer-get-func-getc, lexer-get-func-ungetc,
;   lexer-get-func-line, lexer-get-func-column et lexer-get-func-offset
;

; Taille initiale par defaut du buffer d'entree
(define lexer-init-buffer-len 1024)

; Numero du caractere newline
(define lexer-integer-newline (char->integer #\newline))

; Constructeur d'IS brut
(define lexer-raw-IS-maker
  (lambda (buffer read-ptr input-f counters)
    (let ((input-f          input-f)                ; Entree reelle
	  (buffer           buffer)                 ; Buffer
	  (buflen           (string-length buffer))
	  (read-ptr         read-ptr)
	  (start-ptr        1)                      ; Marque de debut de lexeme
	  (start-line       1)
	  (start-column     1)
	  (start-offset     0)
	  (end-ptr          1)                      ; Marque de fin de lexeme
	  (point-ptr        1)                      ; Le point
	  (user-ptr         1)                      ; Marque de l'usager
	  (user-line        1)
	  (user-column      1)
	  (user-offset      0)
	  (user-up-to-date? #t))                    ; Concerne la colonne seul.
      (letrec
	  ((start-go-to-end-none         ; Fonctions de depl. des marques
	    (lambda ()
	      (set! start-ptr end-ptr)))
	   (start-go-to-end-line
	    (lambda ()
	      (let loop ((ptr start-ptr) (line start-line))
		(if (= ptr end-ptr)
		    (begin
		      (set! start-ptr ptr)
		      (set! start-line line))
		    (if (char=? (string-ref buffer ptr) #\newline)
			(loop (+ ptr 1) (+ line 1))
			(loop (+ ptr 1) line))))))
	   (start-go-to-end-all
	    (lambda ()
	      (set! start-offset (+ start-offset (- end-ptr start-ptr)))
	      (let loop ((ptr start-ptr)
			 (line start-line)
			 (column start-column))
		(if (= ptr end-ptr)
		    (begin
		      (set! start-ptr ptr)
		      (set! start-line line)
		      (set! start-column column))
		    (if (char=? (string-ref buffer ptr) #\newline)
			(loop (+ ptr 1) (+ line 1) 1)
			(loop (+ ptr 1) line (+ column 1)))))))
	   (start-go-to-user-none
	    (lambda ()
	      (set! start-ptr user-ptr)))
	   (start-go-to-user-line
	    (lambda ()
	      (set! start-ptr user-ptr)
	      (set! start-line user-line)))
	   (start-go-to-user-all
	    (lambda ()
	      (set! start-line user-line)
	      (set! start-offset user-offset)
	      (if user-up-to-date?
		  (begin
		    (set! start-ptr user-ptr)
		    (set! start-column user-column))
		  (let loop ((ptr start-ptr) (column start-column))
		    (if (= ptr user-ptr)
			(begin
			  (set! start-ptr ptr)
			  (set! start-column column))
			(if (char=? (string-ref buffer ptr) #\newline)
			    (loop (+ ptr 1) 1)
			    (loop (+ ptr 1) (+ column 1))))))))
	   (end-go-to-point
	    (lambda ()
	      (set! end-ptr point-ptr)))
	   (point-go-to-start
	    (lambda ()
	      (set! point-ptr start-ptr)))
	   (user-go-to-start-none
	    (lambda ()
	      (set! user-ptr start-ptr)))
	   (user-go-to-start-line
	    (lambda ()
	      (set! user-ptr start-ptr)
	      (set! user-line start-line)))
	   (user-go-to-start-all
	    (lambda ()
	      (set! user-ptr start-ptr)
	      (set! user-line start-line)
	      (set! user-column start-column)
	      (set! user-offset start-offset)
	      (set! user-up-to-date? #t)))
	   (init-lexeme-none             ; Debute un nouveau lexeme
	    (lambda ()
	      (if (< start-ptr user-ptr)
		  (start-go-to-user-none))
	      (point-go-to-start)))
	   (init-lexeme-line
	    (lambda ()
	      (if (< start-ptr user-ptr)
		  (start-go-to-user-line))
	      (point-go-to-start)))
	   (init-lexeme-all
	    (lambda ()
	      (if (< start-ptr user-ptr)
		  (start-go-to-user-all))
	      (point-go-to-start)))
	   (get-start-line               ; Obtention des stats du debut du lxm
	    (lambda ()
	      start-line))
	   (get-start-column
	    (lambda ()
	      start-column))
	   (get-start-offset
	    (lambda ()
	      start-offset))
	   (peek-left-context            ; Obtention de caracteres (#f si EOF)
	    (lambda ()
	      (char->integer (string-ref buffer (- start-ptr 1)))))
	   (peek-char
	    (lambda ()
	      (if (< point-ptr read-ptr)
		  (char->integer (string-ref buffer point-ptr))
		  (let ((c (input-f)))
		    (if (char? c)
			(begin
			  (if (= read-ptr buflen)
			      (reorganize-buffer))
			  (string-set! buffer point-ptr c)
			  (set! read-ptr (+ point-ptr 1))
			  (char->integer c))
			(begin
			  (set! input-f (lambda () 'eof))
			  #f))))))
	   (read-char
	    (lambda ()
	      (if (< point-ptr read-ptr)
		  (let ((c (string-ref buffer point-ptr)))
		    (set! point-ptr (+ point-ptr 1))
		    (char->integer c))
		  (let ((c (input-f)))
		    (if (char? c)
			(begin
			  (if (= read-ptr buflen)
			      (reorganize-buffer))
			  (string-set! buffer point-ptr c)
			  (set! read-ptr (+ point-ptr 1))
			  (set! point-ptr read-ptr)
			  (char->integer c))
			(begin
			  (set! input-f (lambda () 'eof))
			  #f))))))
	   (get-start-end-text           ; Obtention du lexeme
	    (lambda ()
	      (substring buffer start-ptr end-ptr)))
	   (get-user-line-line           ; Fonctions pour l'usager
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-line))
	      user-line))
	   (get-user-line-all
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-all))
	      user-line))
	   (get-user-column-all
	    (lambda ()
	      (cond ((< user-ptr start-ptr)
		     (user-go-to-start-all)
		     user-column)
		    (user-up-to-date?
		     user-column)
		    (else
		     (let loop ((ptr start-ptr) (column start-column))
		       (if (= ptr user-ptr)
			   (begin
			     (set! user-column column)
			     (set! user-up-to-date? #t)
			     column)
			   (if (char=? (string-ref buffer ptr) #\newline)
			       (loop (+ ptr 1) 1)
			       (loop (+ ptr 1) (+ column 1)))))))))
	   (get-user-offset-all
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-all))
	      user-offset))
	   (user-getc-none
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-none))
	      (if (< user-ptr read-ptr)
		  (let ((c (string-ref buffer user-ptr)))
		    (set! user-ptr (+ user-ptr 1))
		    c)
		  (let ((c (input-f)))
		    (if (char? c)
			(begin
			  (if (= read-ptr buflen)
			      (reorganize-buffer))
			  (string-set! buffer user-ptr c)
			  (set! read-ptr (+ read-ptr 1))
			  (set! user-ptr read-ptr)
			  c)
			(begin
			  (set! input-f (lambda () 'eof))
			  'eof))))))
	   (user-getc-line
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-line))
	      (if (< user-ptr read-ptr)
		  (let ((c (string-ref buffer user-ptr)))
		    (set! user-ptr (+ user-ptr 1))
		    (if (char=? c #\newline)
			(set! user-line (+ user-line 1)))
		    c)
		  (let ((c (input-f)))
		    (if (char? c)
			(begin
			  (if (= read-ptr buflen)
			      (reorganize-buffer))
			  (string-set! buffer user-ptr c)
			  (set! read-ptr (+ read-ptr 1))
			  (set! user-ptr read-ptr)
			  (if (char=? c #\newline)
			      (set! user-line (+ user-line 1)))
			  c)
			(begin
			  (set! input-f (lambda () 'eof))
			  'eof))))))
	   (user-getc-all
	    (lambda ()
	      (if (< user-ptr start-ptr)
		  (user-go-to-start-all))
	      (if (< user-ptr read-ptr)
		  (let ((c (string-ref buffer user-ptr)))
		    (set! user-ptr (+ user-ptr 1))
		    (if (char=? c #\newline)
			(begin
			  (set! user-line (+ user-line 1))
			  (set! user-column 1))
			(set! user-column (+ user-column 1)))
		    (set! user-offset (+ user-offset 1))
		    c)
		  (let ((c (input-f)))
		    (if (char? c)
			(begin
			  (if (= read-ptr buflen)
			      (reorganize-buffer))
			  (string-set! buffer user-ptr c)
			  (set! read-ptr (+ read-ptr 1))
			  (set! user-ptr read-ptr)
			  (if (char=? c #\newline)
			      (begin
				(set! user-line (+ user-line 1))
				(set! user-column 1))
			      (set! user-column (+ user-column 1)))
			  (set! user-offset (+ user-offset 1))
			  c)
			(begin
			  (set! input-f (lambda () 'eof))
			  'eof))))))
	   (user-ungetc-none
	    (lambda ()
	      (if (> user-ptr start-ptr)
		  (set! user-ptr (- user-ptr 1)))))
	   (user-ungetc-line
	    (lambda ()
	      (if (> user-ptr start-ptr)
		  (begin
		    (set! user-ptr (- user-ptr 1))
		    (let ((c (string-ref buffer user-ptr)))
		      (if (char=? c #\newline)
			  (set! user-line (- user-line 1))))))))
	   (user-ungetc-all
	    (lambda ()
	      (if (> user-ptr start-ptr)
		  (begin
		    (set! user-ptr (- user-ptr 1))
		    (let ((c (string-ref buffer user-ptr)))
		      (if (char=? c #\newline)
			  (begin
			    (set! user-line (- user-line 1))
			    (set! user-up-to-date? #f))
			  (set! user-column (- user-column 1)))
		      (set! user-offset (- user-offset 1)))))))
	   (reorganize-buffer            ; Decaler ou agrandir le buffer
	    (lambda ()
	      (if (< (* 2 start-ptr) buflen)
		  (let* ((newlen (* 2 buflen))
			 (newbuf (make-string newlen))
			 (delta (- start-ptr 1)))
		    (let loop ((from (- start-ptr 1)))
		      (if (< from buflen)
			  (begin
			    (string-set! newbuf
					 (- from delta)
					 (string-ref buffer from))
			    (loop (+ from 1)))))
		    (set! buffer    newbuf)
		    (set! buflen    newlen)
		    (set! read-ptr  (- read-ptr delta))
		    (set! start-ptr (- start-ptr delta))
		    (set! end-ptr   (- end-ptr delta))
		    (set! point-ptr (- point-ptr delta))
		    (set! user-ptr  (- user-ptr delta)))
		  (let ((delta (- start-ptr 1)))
		    (let loop ((from (- start-ptr 1)))
		      (if (< from buflen)
			  (begin
			    (string-set! buffer
					 (- from delta)
					 (string-ref buffer from))
			    (loop (+ from 1)))))
		    (set! read-ptr  (- read-ptr delta))
		    (set! start-ptr (- start-ptr delta))
		    (set! end-ptr   (- end-ptr delta))
		    (set! point-ptr (- point-ptr delta))
		    (set! user-ptr  (- user-ptr delta)))))))
	(list (cons 'start-go-to-end
		    (cond ((eq? counters 'none) start-go-to-end-none)
			  ((eq? counters 'line) start-go-to-end-line)
			  ((eq? counters 'all ) start-go-to-end-all)))
	      (cons 'end-go-to-point
		    end-go-to-point)
	      (cons 'init-lexeme
		    (cond ((eq? counters 'none) init-lexeme-none)
			  ((eq? counters 'line) init-lexeme-line)
			  ((eq? counters 'all ) init-lexeme-all)))
	      (cons 'get-start-line
		    get-start-line)
	      (cons 'get-start-column
		    get-start-column)
	      (cons 'get-start-offset
		    get-start-offset)
	      (cons 'peek-left-context
		    peek-left-context)
	      (cons 'peek-char
		    peek-char)
	      (cons 'read-char
		    read-char)
	      (cons 'get-start-end-text
		    get-start-end-text)
	      (cons 'get-user-line
		    (cond ((eq? counters 'none) #f)
			  ((eq? counters 'line) get-user-line-line)
			  ((eq? counters 'all ) get-user-line-all)))
	      (cons 'get-user-column
		    (cond ((eq? counters 'none) #f)
			  ((eq? counters 'line) #f)
			  ((eq? counters 'all ) get-user-column-all)))
	      (cons 'get-user-offset
		    (cond ((eq? counters 'none) #f)
			  ((eq? counters 'line) #f)
			  ((eq? counters 'all ) get-user-offset-all)))
	      (cons 'user-getc
		    (cond ((eq? counters 'none) user-getc-none)
			  ((eq? counters 'line) user-getc-line)
			  ((eq? counters 'all ) user-getc-all)))
	      (cons 'user-ungetc
		    (cond ((eq? counters 'none) user-ungetc-none)
			  ((eq? counters 'line) user-ungetc-line)
			  ((eq? counters 'all ) user-ungetc-all))))))))

; Construit un Input System
; Le premier parametre doit etre parmi "port", "procedure" ou "string"
; Prend un parametre facultatif qui doit etre parmi
; "none", "line" ou "all"
(define lexer-make-IS
  (lambda (input-type input . largs)
    (let ((counters-type (cond ((null? largs)
				'line)
			       ((memq (car largs) '(none line all))
				(car largs))
			       (else
				'line))))
      (cond ((and (eq? input-type 'port) (input-port? input))
	     (let* ((buffer   (make-string lexer-init-buffer-len #\newline))
		    (read-ptr 1)
		    (input-f  (lambda () (read-char input))))
	       (lexer-raw-IS-maker buffer read-ptr input-f counters-type)))
	    ((and (eq? input-type 'procedure) (procedure? input))
	     (let* ((buffer   (make-string lexer-init-buffer-len #\newline))
		    (read-ptr 1)
		    (input-f  input))
	       (lexer-raw-IS-maker buffer read-ptr input-f counters-type)))
	    ((and (eq? input-type 'string) (string? input))
	     (let* ((buffer   (string-append (string #\newline) input))
		    (read-ptr (string-length buffer))
		    (input-f  (lambda () 'eof)))
	       (lexer-raw-IS-maker buffer read-ptr input-f counters-type)))
	    (else
	     (let* ((buffer   (string #\newline))
		    (read-ptr 1)
		    (input-f  (lambda () 'eof)))
	       (lexer-raw-IS-maker buffer read-ptr input-f counters-type)))))))

; Les fonctions:
;   lexer-get-func-getc, lexer-get-func-ungetc,
;   lexer-get-func-line, lexer-get-func-column et lexer-get-func-offset
(define lexer-get-func-getc
  (lambda (IS) (cdr (assq 'user-getc IS))))
(define lexer-get-func-ungetc
  (lambda (IS) (cdr (assq 'user-ungetc IS))))
(define lexer-get-func-line
  (lambda (IS) (cdr (assq 'get-user-line IS))))
(define lexer-get-func-column
  (lambda (IS) (cdr (assq 'get-user-column IS))))
(define lexer-get-func-offset
  (lambda (IS) (cdr (assq 'get-user-offset IS))))

;
; Gestion des lexers
;

; Fabrication de lexer a partir d'arbres de decision
(define lexer-make-tree-lexer
  (lambda (tables IS)
    (letrec
	(; Contenu de la table
	 (counters-type        (vector-ref tables 0))
	 (<<EOF>>-pre-action   (vector-ref tables 1))
	 (<<ERROR>>-pre-action (vector-ref tables 2))
	 (rules-pre-actions    (vector-ref tables 3))
	 (table-nl-start       (vector-ref tables 5))
	 (table-no-nl-start    (vector-ref tables 6))
	 (trees-v              (vector-ref tables 7))
	 (acc-v                (vector-ref tables 8))

	 ; Contenu du IS
	 (IS-start-go-to-end    (cdr (assq 'start-go-to-end IS)))
	 (IS-end-go-to-point    (cdr (assq 'end-go-to-point IS)))
	 (IS-init-lexeme        (cdr (assq 'init-lexeme IS)))
	 (IS-get-start-line     (cdr (assq 'get-start-line IS)))
	 (IS-get-start-column   (cdr (assq 'get-start-column IS)))
	 (IS-get-start-offset   (cdr (assq 'get-start-offset IS)))
	 (IS-peek-left-context  (cdr (assq 'peek-left-context IS)))
	 (IS-peek-char          (cdr (assq 'peek-char IS)))
	 (IS-read-char          (cdr (assq 'read-char IS)))
	 (IS-get-start-end-text (cdr (assq 'get-start-end-text IS)))
	 (IS-get-user-line      (cdr (assq 'get-user-line IS)))
	 (IS-get-user-column    (cdr (assq 'get-user-column IS)))
	 (IS-get-user-offset    (cdr (assq 'get-user-offset IS)))
	 (IS-user-getc          (cdr (assq 'user-getc IS)))
	 (IS-user-ungetc        (cdr (assq 'user-ungetc IS)))

	 ; Resultats
	 (<<EOF>>-action   #f)
	 (<<ERROR>>-action #f)
	 (rules-actions    #f)
	 (states           #f)
	 (final-lexer      #f)

	 ; Gestion des hooks
	 (hook-list '())
	 (add-hook
	  (lambda (thunk)
	    (set! hook-list (cons thunk hook-list))))
	 (apply-hooks
	  (lambda ()
	    (let loop ((l hook-list))
	      (if (pair? l)
		  (begin
		    ((car l))
		    (loop (cdr l)))))))

	 ; Preparation des actions
	 (set-action-statics
	  (lambda (pre-action)
	    (pre-action final-lexer IS-user-getc IS-user-ungetc)))
	 (prepare-special-action-none
	  (lambda (pre-action)
	    (let ((action #f))
	      (let ((result
		     (lambda ()
		       (action "")))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-special-action-line
	  (lambda (pre-action)
	    (let ((action #f))
	      (let ((result
		     (lambda (yyline)
		       (action "" yyline)))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-special-action-all
	  (lambda (pre-action)
	    (let ((action #f))
	      (let ((result
		     (lambda (yyline yycolumn yyoffset)
		       (action "" yyline yycolumn yyoffset)))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-special-action
	  (lambda (pre-action)
	    (cond ((eq? counters-type 'none)
		   (prepare-special-action-none pre-action))
		  ((eq? counters-type 'line)
		   (prepare-special-action-line pre-action))
		  ((eq? counters-type 'all)
		   (prepare-special-action-all  pre-action)))))
	 (prepare-action-yytext-none
	  (lambda (pre-action)
	    (let ((get-start-end-text IS-get-start-end-text)
		  (start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda ()
		       (let ((yytext (get-start-end-text)))
			 (start-go-to-end)
			 (action yytext))))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-yytext-line
	  (lambda (pre-action)
	    (let ((get-start-end-text IS-get-start-end-text)
		  (start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda (yyline)
		       (let ((yytext (get-start-end-text)))
			 (start-go-to-end)
			 (action yytext yyline))))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-yytext-all
	  (lambda (pre-action)
	    (let ((get-start-end-text IS-get-start-end-text)
		  (start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda (yyline yycolumn yyoffset)
		       (let ((yytext (get-start-end-text)))
			 (start-go-to-end)
			 (action yytext yyline yycolumn yyoffset))))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-yytext
	  (lambda (pre-action)
	    (cond ((eq? counters-type 'none)
		   (prepare-action-yytext-none pre-action))
		  ((eq? counters-type 'line)
		   (prepare-action-yytext-line pre-action))
		  ((eq? counters-type 'all)
		   (prepare-action-yytext-all  pre-action)))))
	 (prepare-action-no-yytext-none
	  (lambda (pre-action)
	    (let ((start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda ()
		       (start-go-to-end)
		       (action)))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-no-yytext-line
	  (lambda (pre-action)
	    (let ((start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda (yyline)
		       (start-go-to-end)
		       (action yyline)))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-no-yytext-all
	  (lambda (pre-action)
	    (let ((start-go-to-end    IS-start-go-to-end)
		  (action             #f))
	      (let ((result
		     (lambda (yyline yycolumn yyoffset)
		       (start-go-to-end)
		       (action yyline yycolumn yyoffset)))
		    (hook
		     (lambda ()
		       (set! action (set-action-statics pre-action)))))
		(add-hook hook)
		result))))
	 (prepare-action-no-yytext
	  (lambda (pre-action)
	    (cond ((eq? counters-type 'none)
		   (prepare-action-no-yytext-none pre-action))
		  ((eq? counters-type 'line)
		   (prepare-action-no-yytext-line pre-action))
		  ((eq? counters-type 'all)
		   (prepare-action-no-yytext-all  pre-action)))))

	 ; Fabrique les fonctions de dispatch
	 (prepare-dispatch-err
	  (lambda (leaf)
	    (lambda (c)
	      #f)))
	 (prepare-dispatch-number
	  (lambda (leaf)
	    (let ((state-function #f))
	      (let ((result
		     (lambda (c)
		       state-function))
		    (hook
		     (lambda ()
		       (set! state-function (vector-ref states leaf)))))
		(add-hook hook)
		result))))
	 (prepare-dispatch-leaf
	  (lambda (leaf)
	    (if (eq? leaf 'err)
		(prepare-dispatch-err leaf)
		(prepare-dispatch-number leaf))))
	 (prepare-dispatch-<
	  (lambda (tree)
	    (let ((left-tree  (list-ref tree 1))
		  (right-tree (list-ref tree 2)))
	      (let ((bound      (list-ref tree 0))
		    (left-func  (prepare-dispatch-tree left-tree))
		    (right-func (prepare-dispatch-tree right-tree)))
		(lambda (c)
		  (if (< c bound)
		      (left-func c)
		      (right-func c)))))))
	 (prepare-dispatch-=
	  (lambda (tree)
	    (let ((left-tree  (list-ref tree 2))
		  (right-tree (list-ref tree 3)))
	      (let ((bound      (list-ref tree 1))
		    (left-func  (prepare-dispatch-tree left-tree))
		    (right-func (prepare-dispatch-tree right-tree)))
		(lambda (c)
		  (if (= c bound)
		      (left-func c)
		      (right-func c)))))))
	 (prepare-dispatch-tree
	  (lambda (tree)
	    (cond ((not (pair? tree))
		   (prepare-dispatch-leaf tree))
		  ((eq? (car tree) '=)
		   (prepare-dispatch-= tree))
		  (else
		   (prepare-dispatch-< tree)))))
	 (prepare-dispatch
	  (lambda (tree)
	    (let ((dicho-func (prepare-dispatch-tree tree)))
	      (lambda (c)
		(and c (dicho-func c))))))

	 ; Fabrique les fonctions de transition (read & go) et (abort)
	 (prepare-read-n-go
	  (lambda (tree)
	    (let ((dispatch-func (prepare-dispatch tree))
		  (read-char     IS-read-char))
	      (lambda ()
		(dispatch-func (read-char))))))
	 (prepare-abort
	  (lambda (tree)
	    (lambda ()
	      #f)))
	 (prepare-transition
	  (lambda (tree)
	    (if (eq? tree 'err)
		(prepare-abort     tree)
		(prepare-read-n-go tree))))

	 ; Fabrique les fonctions d'etats ([set-end] & trans)
	 (prepare-state-no-acc
	   (lambda (s r1 r2)
	     (let ((trans-func (prepare-transition (vector-ref trees-v s))))
	       (lambda (action)
		 (let ((next-state (trans-func)))
		   (if next-state
		       (next-state action)
		       action))))))
	 (prepare-state-yes-no
	  (lambda (s r1 r2)
	    (let ((peek-char       IS-peek-char)
		  (end-go-to-point IS-end-go-to-point)
		  (new-action1     #f)
		  (trans-func (prepare-transition (vector-ref trees-v s))))
	      (let ((result
		     (lambda (action)
		       (let* ((c (peek-char))
			      (new-action
			       (if (or (not c) (= c lexer-integer-newline))
				   (begin
				     (end-go-to-point)
				     new-action1)
				   action))
			      (next-state (trans-func)))
			 (if next-state
			     (next-state new-action)
			     new-action))))
		    (hook
		     (lambda ()
		       (set! new-action1 (vector-ref rules-actions r1)))))
		(add-hook hook)
		result))))
	 (prepare-state-diff-acc
	  (lambda (s r1 r2)
	    (let ((end-go-to-point IS-end-go-to-point)
		  (peek-char       IS-peek-char)
		  (new-action1     #f)
		  (new-action2     #f)
		  (trans-func (prepare-transition (vector-ref trees-v s))))
	      (let ((result
		     (lambda (action)
		       (end-go-to-point)
		       (let* ((c (peek-char))
			      (new-action
			       (if (or (not c) (= c lexer-integer-newline))
				   new-action1
				   new-action2))
			      (next-state (trans-func)))
			 (if next-state
			     (next-state new-action)
			     new-action))))
		    (hook
		     (lambda ()
		       (set! new-action1 (vector-ref rules-actions r1))
		       (set! new-action2 (vector-ref rules-actions r2)))))
		(add-hook hook)
		result))))
	 (prepare-state-same-acc
	  (lambda (s r1 r2)
	    (let ((end-go-to-point IS-end-go-to-point)
		  (trans-func (prepare-transition (vector-ref trees-v s)))
		  (new-action #f))
	      (let ((result
		     (lambda (action)
		       (end-go-to-point)
		       (let ((next-state (trans-func)))
			 (if next-state
			     (next-state new-action)
			     new-action))))
		    (hook
		     (lambda ()
		       (set! new-action (vector-ref rules-actions r1)))))
		(add-hook hook)
		result))))
	 (prepare-state
	  (lambda (s)
	    (let* ((acc (vector-ref acc-v s))
		   (r1 (car acc))
		   (r2 (cdr acc)))
	      (cond ((not r1)  (prepare-state-no-acc   s r1 r2))
		    ((not r2)  (prepare-state-yes-no   s r1 r2))
		    ((< r1 r2) (prepare-state-diff-acc s r1 r2))
		    (else      (prepare-state-same-acc s r1 r2))))))

	 ; Fabrique la fonction de lancement du lexage a l'etat de depart
	 (prepare-start-same
	  (lambda (s1 s2)
	    (let ((peek-char    IS-peek-char)
		  (eof-action   #f)
		  (start-state  #f)
		  (error-action #f))
	      (let ((result
		     (lambda ()
		       (if (not (peek-char))
			   eof-action
			   (start-state error-action))))
		    (hook
		     (lambda ()
		       (set! eof-action   <<EOF>>-action)
		       (set! start-state  (vector-ref states s1))
		       (set! error-action <<ERROR>>-action))))
		(add-hook hook)
		result))))
	 (prepare-start-diff
	  (lambda (s1 s2)
	    (let ((peek-char         IS-peek-char)
		  (eof-action        #f)
		  (peek-left-context IS-peek-left-context)
		  (start-state1      #f)
		  (start-state2      #f)
		  (error-action      #f))
	      (let ((result
		     (lambda ()
		       (cond ((not (peek-char))
			      eof-action)
			     ((= (peek-left-context) lexer-integer-newline)
			      (start-state1 error-action))
			     (else
			      (start-state2 error-action)))))
		    (hook
		     (lambda ()
		       (set! eof-action <<EOF>>-action)
		       (set! start-state1 (vector-ref states s1))
		       (set! start-state2 (vector-ref states s2))
		       (set! error-action <<ERROR>>-action))))
		(add-hook hook)
		result))))
	 (prepare-start
	  (lambda ()
	    (let ((s1 table-nl-start)
		  (s2 table-no-nl-start))
	      (if (= s1 s2)
		  (prepare-start-same s1 s2)
		  (prepare-start-diff s1 s2)))))

	 ; Fabrique la fonction principale
	 (prepare-lexer-none
	  (lambda ()
	    (let ((init-lexeme IS-init-lexeme)
		  (start-func  (prepare-start)))
	      (lambda ()
		(init-lexeme)
		((start-func))))))
	 (prepare-lexer-line
	  (lambda ()
	    (let ((init-lexeme    IS-init-lexeme)
		  (get-start-line IS-get-start-line)
		  (start-func     (prepare-start)))
	      (lambda ()
		(init-lexeme)
		(let ((yyline (get-start-line)))
		  ((start-func) yyline))))))
	 (prepare-lexer-all
	  (lambda ()
	    (let ((init-lexeme      IS-init-lexeme)
		  (get-start-line   IS-get-start-line)
		  (get-start-column IS-get-start-column)
		  (get-start-offset IS-get-start-offset)
		  (start-func       (prepare-start)))
	      (lambda ()
		(init-lexeme)
		(let ((yyline   (get-start-line))
		      (yycolumn (get-start-column))
		      (yyoffset (get-start-offset)))
		  ((start-func) yyline yycolumn yyoffset))))))
	 (prepare-lexer
	  (lambda ()
	    (cond ((eq? counters-type 'none) (prepare-lexer-none))
		  ((eq? counters-type 'line) (prepare-lexer-line))
		  ((eq? counters-type 'all)  (prepare-lexer-all))))))

      ; Calculer la valeur de <<EOF>>-action et de <<ERROR>>-action
      (set! <<EOF>>-action   (prepare-special-action <<EOF>>-pre-action))
      (set! <<ERROR>>-action (prepare-special-action <<ERROR>>-pre-action))

      ; Calculer la valeur de rules-actions
      (let* ((len (quotient (vector-length rules-pre-actions) 2))
	     (v (make-vector len)))
	(let loop ((r (- len 1)))
	  (if (< r 0)
	      (set! rules-actions v)
	      (let* ((yytext? (vector-ref rules-pre-actions (* 2 r)))
		     (pre-action (vector-ref rules-pre-actions (+ (* 2 r) 1)))
		     (action (if yytext?
				 (prepare-action-yytext    pre-action)
				 (prepare-action-no-yytext pre-action))))
		(vector-set! v r action)
		(loop (- r 1))))))

      ; Calculer la valeur de states
      (let* ((len (vector-length trees-v))
	     (v (make-vector len)))
	(let loop ((s (- len 1)))
	  (if (< s 0)
	      (set! states v)
	      (begin
		(vector-set! v s (prepare-state s))
		(loop (- s 1))))))

      ; Calculer la valeur de final-lexer
      (set! final-lexer (prepare-lexer))

      ; Executer les hooks
      (apply-hooks)

      ; Resultat
      final-lexer)))

; Fabrication de lexer a partir de listes de caracteres taggees
(define lexer-make-char-lexer
  (let* ((char->class
	  (lambda (c)
	    (let ((n (char->integer c)))
	      (list (cons n n)))))
	 (merge-sort
	  (lambda (l combine zero-elt)
	    (if (null? l)
		zero-elt
		(let loop1 ((l l))
		  (if (null? (cdr l))
		      (car l)
		      (loop1
		       (let loop2 ((l l))
			 (cond ((null? l)
				l)
			       ((null? (cdr l))
				l)
			       (else
				(cons (combine (car l) (cadr l))
				      (loop2 (cddr l))))))))))))
	 (finite-class-union
	  (lambda (c1 c2)
	    (let loop ((c1 c1) (c2 c2) (u '()))
	      (if (null? c1)
		  (if (null? c2)
		      (reverse u)
		      (loop c1 (cdr c2) (cons (car c2) u)))
		  (if (null? c2)
		      (loop (cdr c1) c2 (cons (car c1) u))
		      (let* ((r1 (car c1))
			     (r2 (car c2))
			     (r1start (car r1))
			     (r1end (cdr r1))
			     (r2start (car r2))
			     (r2end (cdr r2)))
			(if (<= r1start r2start)
			    (cond ((< (+ r1end 1) r2start)
				   (loop (cdr c1) c2 (cons r1 u)))
				  ((<= r1end r2end)
				   (loop (cdr c1)
					 (cons (cons r1start r2end) (cdr c2))
					 u))
				  (else
				   (loop c1 (cdr c2) u)))
			    (cond ((> r1start (+ r2end 1))
				   (loop c1 (cdr c2) (cons r2 u)))
				  ((>= r1end r2end)
				   (loop (cons (cons r2start r1end) (cdr c1))
					 (cdr c2)
					 u))
				  (else
				   (loop (cdr c1) c2 u))))))))))
	 (char-list->class
	  (lambda (cl)
	    (let ((classes (map char->class cl)))
	      (merge-sort classes finite-class-union '()))))
	 (class-<
	  (lambda (b1 b2)
	    (cond ((eq? b1 'inf+) #f)
		  ((eq? b2 'inf-) #f)
		  ((eq? b1 'inf-) #t)
		  ((eq? b2 'inf+) #t)
		  (else (< b1 b2)))))
	 (finite-class-compl
	  (lambda (c)
	    (let loop ((c c) (start 'inf-))
	      (if (null? c)
		  (list (cons start 'inf+))
		  (let* ((r (car c))
			 (rstart (car r))
			 (rend (cdr r)))
		    (if (class-< start rstart)
			(cons (cons start (- rstart 1))
			      (loop c rstart))
			(loop (cdr c) (+ rend 1))))))))
	 (tagged-chars->class
	  (lambda (tcl)
	    (let* ((inverse? (car tcl))
		   (cl (cdr tcl))
		   (class-tmp (char-list->class cl)))
	      (if inverse? (finite-class-compl class-tmp) class-tmp))))
	 (charc->arc
	  (lambda (charc)
	    (let* ((tcl (car charc))
		   (dest (cdr charc))
		   (class (tagged-chars->class tcl)))
	      (cons class dest))))
	 (arc->sharcs
	  (lambda (arc)
	    (let* ((range-l (car arc))
		   (dest (cdr arc))
		   (op (lambda (range) (cons range dest))))
	      (map op range-l))))
	 (class-<=
	  (lambda (b1 b2)
	    (cond ((eq? b1 'inf-) #t)
		  ((eq? b2 'inf+) #t)
		  ((eq? b1 'inf+) #f)
		  ((eq? b2 'inf-) #f)
		  (else (<= b1 b2)))))
	 (sharc-<=
	  (lambda (sharc1 sharc2)
	    (class-<= (caar sharc1) (caar sharc2))))
	 (merge-sharcs
	  (lambda (l1 l2)
	    (let loop ((l1 l1) (l2 l2))
	      (cond ((null? l1)
		     l2)
		    ((null? l2)
		     l1)
		    (else
		     (let ((sharc1 (car l1))
			   (sharc2 (car l2)))
		       (if (sharc-<= sharc1 sharc2)
			   (cons sharc1 (loop (cdr l1) l2))
			   (cons sharc2 (loop l1 (cdr l2))))))))))
	 (class-= eqv?)
	 (fill-error
	  (lambda (sharcs)
	    (let loop ((sharcs sharcs) (start 'inf-))
	      (cond ((class-= start 'inf+)
		     '())
		    ((null? sharcs)
		     (cons (cons (cons start 'inf+) 'err)
			   (loop sharcs 'inf+)))
		    (else
		     (let* ((sharc (car sharcs))
			    (h (caar sharc))
			    (t (cdar sharc)))
		       (if (class-< start h)
			   (cons (cons (cons start (- h 1)) 'err)
				 (loop sharcs h))
			   (cons sharc (loop (cdr sharcs)
					     (if (class-= t 'inf+)
						 'inf+
						 (+ t 1)))))))))))
	 (charcs->tree
	  (lambda (charcs)
	    (let* ((op (lambda (charc) (arc->sharcs (charc->arc charc))))
		   (sharcs-l (map op charcs))
		   (sorted-sharcs (merge-sort sharcs-l merge-sharcs '()))
		   (full-sharcs (fill-error sorted-sharcs))
		   (op (lambda (sharc) (cons (caar sharc) (cdr sharc))))
		   (table (list->vector (map op full-sharcs))))
	      (let loop ((left 0) (right (- (vector-length table) 1)))
		(if (= left right)
		    (cdr (vector-ref table left))
		    (let ((mid (quotient (+ left right 1) 2)))
		      (if (and (= (+ left 2) right)
			       (= (+ (car (vector-ref table mid)) 1)
				  (car (vector-ref table right)))
			       (eqv? (cdr (vector-ref table left))
				     (cdr (vector-ref table right))))
			  (list '=
				(car (vector-ref table mid))
				(cdr (vector-ref table mid))
				(cdr (vector-ref table left)))
			  (list (car (vector-ref table mid))
				(loop left (- mid 1))
				(loop mid right))))))))))
    (lambda (tables IS)
      (let ((counters         (vector-ref tables 0))
	    (<<EOF>>-action   (vector-ref tables 1))
	    (<<ERROR>>-action (vector-ref tables 2))
	    (rules-actions    (vector-ref tables 3))
	    (nl-start         (vector-ref tables 5))
	    (no-nl-start      (vector-ref tables 6))
	    (charcs-v         (vector-ref tables 7))
	    (acc-v            (vector-ref tables 8)))
	(let* ((len (vector-length charcs-v))
	       (v (make-vector len)))
	  (let loop ((i (- len 1)))
	    (if (>= i 0)
		(begin
		  (vector-set! v i (charcs->tree (vector-ref charcs-v i)))
		  (loop (- i 1)))
		(lexer-make-tree-lexer
		 (vector counters
			 <<EOF>>-action
			 <<ERROR>>-action
			 rules-actions
			 'decision-trees
			 nl-start
			 no-nl-start
			 v
			 acc-v)
		 IS))))))))

; Fabrication d'un lexer a partir de code pre-genere
(define lexer-make-code-lexer
  (lambda (tables IS)
    (let ((<<EOF>>-pre-action   (vector-ref tables 1))
	  (<<ERROR>>-pre-action (vector-ref tables 2))
	  (rules-pre-action     (vector-ref tables 3))
	  (code                 (vector-ref tables 5)))
      (code <<EOF>>-pre-action <<ERROR>>-pre-action rules-pre-action IS))))

(define lexer-make-lexer
  (lambda (tables IS)
    (let ((automaton-type (vector-ref tables 4)))
      (cond ((eq? automaton-type 'decision-trees)
	     (lexer-make-tree-lexer tables IS))
	    ((eq? automaton-type 'tagged-chars-lists)
	     (lexer-make-char-lexer tables IS))
	    ((eq? automaton-type 'code)
	     (lexer-make-code-lexer tables IS))))))

;
; Table generated from the file NineML.l by SILex 1.0
;

(define lexer-default-table
  (vector
   'line
   (lambda (yycontinue yygetc yyungetc)
     (lambda (yytext yyline)
                                   '*eoi*
       ))
   (lambda (yycontinue yygetc yyungetc)
     (lambda (yytext yyline)
                                   (lexer-error (conc yyline ": illegal character") (yygetc))
       ))
   (vector
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                 (tok yyline MODULE)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                 (tok yyline VALUE)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline FUNCTION)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline FUNCTION)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline RETURN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline RETURN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline LET)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline STRUCT)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline END)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline FUNCTOR)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline TYPE)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline SIG)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline IN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline IF)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline THEN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                   (tok yyline ELSE)
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                                   (tok yyline IDENT (ident-create yytext))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                                   (tok yyline LABEL (string->symbol (substring yytext 1 (string-length yytext))))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                           (tok yyline NAT (string->number (substring yytext 2 (string-length yytext)) 16))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                           (tok yyline NAT (string->number (substring yytext 2 (string-length yytext)) 8))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                           (tok yyline NAT (string->number (substring yytext 2 (string-length yytext)) 2))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                           (tok yyline NAT (string->number (substring yytext 2 (string-length yytext)) 10))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                                                         (tok yyline REAL (string->number yytext))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                                           (tok yyline NAT (string->number yytext))
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                 (let loop ([cs '()])
                                      (let ([c (yygetc)])
                                        (cond [(eq? 'eof c)   (lexer-error "unexpected end of string constant")]
                                              [(char=? c #\\) (let ((n (yygetc)))
                                                                (loop (cons n cs)))]
                                              [(char=? c #\") (tok yyline STRING (reverse-list->string cs))] 
                                              [else (loop (cons c cs))])))
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                          (let loop ((kont (lambda (x) (tok yyline SEXPR (make-sexpr-macro #f x))))
				     (result '(#\()))
                             (let ((c (yygetc)))
                               (cond ((eq? 'eof c)    (lexer-error "unexpected end of expression"))
                                     ((char=? #\] c)  (kont (cons #\) result)))
                                     ((char=? #\[ c)  (loop (lambda (x) (loop kont (append x result))) '(#\()))
                                     (else            (loop kont (cons c result)))
                                     )))
        ))
    #t
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yytext yyline)
                         (let ((label (substring yytext 2 (- (string-length yytext) 1))))
			    (let loop ((kont (lambda (x) (tok yyline SEXPR (make-sexpr-macro label x))))
				       (result '(#\()))
                             (let ((c (yygetc)))
                               (cond ((eq? 'eof c)    (lexer-error "unexpected end of expression"))
                                     ((char=? #\] c)  (kont (cons #\) result)))
                                     ((char=? #\[ c)  (loop (lambda (x) (loop kont (append x result))) '(#\()))
                                     (else            (loop kont (cons c result)))
                                     ))
			     ))
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                           (let loop ((kont (lambda (x) (tok yyline QEXPR x))) 
				      (result '(#\()))
                             (let ((c (yygetc)))
                               (cond ((eq? 'eof c)    (lexer-error "unexpected end of expression"))
                                     ((char=? #\] c)  (kont (cons #\) result)))
                                     ((char=? #\[ c)  (loop (lambda (x) (loop kont (append x result))) '(#\()))
                                     (else            (loop kont (cons c result)))
                                     )))
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                           (let loop ((kont yycontinue))
                             (let ((c (yygetc)))
                               (cond ((eq? 'eof c) (lexer-error "unexpected end of comment"))
                                     ((and (char=? #\* c) (char=? #\) (yygetc))) (kont))
                                     ((and (char=? #\( c) (char=? #\* (yygetc))) (loop (lambda () (loop kont))))
                                     (else (loop kont)))))
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline LPAREN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline RPAREN)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline DOT)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline SEMICOLON)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline ARROW)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline DARROW)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline EQUAL)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline COMMA)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline QUOTE)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline COLON)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline STAR)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline PLUS)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline MINUS)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline SLASH)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline EQEQ)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline LG)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline LESS)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline GREATER)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline LEQ)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (tok yyline GEQ)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (yycontinue)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (yycontinue)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (yycontinue)
        ))
    #f
    (lambda (yycontinue yygetc yyungetc)
      (lambda (yyline)
                                   (yycontinue)
        )))
   'decision-trees
   0
   0
   '#((62 (41 (32 (11 (9 err (10 3 4)) (= 13 2 err)) (35 (33 1 (34 err 20))
    (39 (36 17 err) (40 11 16)))) (47 (44 (42 15 (43 9 8)) (45 12 (46 23
    22))) (58 (48 7 (49 24 21)) (60 (59 10 14) (61 6 13))))) (103 (96 (65
    (63 5 (64 err 18)) (91 26 (92 19 err))) (99 (97 25 (98 26 34)) (101
    (100 37 26) (102 29 33)))) (114 (108 (= 105 27 26) (109 31 (110 36
    26))) (117 (115 32 (116 30 28)) (119 (118 26 35) (123 26 err)))))) (=
    32 1 err) (= 13 2 err) (= 9 3 err) (= 10 4 err) (= 61 38 err) (62 (61
    err 39) (63 40 err)) err err err err err err (62 (61 err 41) (63 42
    err)) err err (= 42 43 err) (= 91 44 err) (97 err (123 45 err)) err err
    (47 (46 err 46) (48 err (58 21 err))) (48 err (58 47 err)) (48 (= 46 50
    err) (62 (58 49 err) (63 48 err))) (80 (66 (47 (46 err 46) (48 err (58
    21 err))) (68 (67 52 err) (69 51 (79 err 53)))) (100 (89 (88 err 54) (=
    98 52 err)) (112 (101 51 (111 err 53)) (= 120 54 err)))) (91 (65 err
    55) (97 err (123 55 err))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err
    26) (97 err (123 26 err)))) (96 (65 (48 err (58 26 err)) (91 26 (95 err
    26))) (103 (97 err (102 26 56)) (111 (110 26 57) (123 26 err)))) (96
    (65 (48 err (58 26 err)) (91 26 (95 err 26))) (105 (97 err (104 26 58))
    (122 (121 26 59) (123 26 err)))) (96 (65 (48 err (58 26 err)) (91 26
    (95 err 26))) (109 (97 err (108 26 60)) (111 (110 26 61) (123 26
    err)))) (96 (65 (48 err (58 26 err)) (91 26 (95 err 26))) (106 (97 err
    (105 26 62)) (117 (116 26 63) (123 26 err)))) (95 (58 (48 err 26) (65
    err (91 26 err))) (101 (= 96 err 26) (102 64 (123 26 err)))) (95 (58
    (48 err 26) (65 err (91 26 err))) (101 (= 96 err 26) (102 65 (123 26
    err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (117 (= 96 err 26)
    (118 66 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (105
    (= 96 err 26) (106 67 (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (97 (96 26 err) (98 68 (123 26 err)))) (95 (58 (48 err 26)
    (65 err (91 26 err))) (111 (= 96 err 26) (112 69 (123 26 err)))) (95
    (58 (48 err 26) (65 err (91 26 err))) (111 (= 96 err 26) (112 70 (123
    26 err)))) err err err err err err err (= 91 71 err) (69 (48 err (58 46
    err)) (101 (70 72 err) (102 72 err))) (69 (48 err (58 47 err)) (101 (70
    72 err) (102 72 err))) err (47 (46 err 46) (48 err (58 49 err))) (48
    err (58 47 err)) (48 err (58 73 err)) (48 err (50 74 err)) (48 err (56
    75 err)) (65 (48 err (58 76 err)) (97 (71 76 err) (103 76 err))) (91
    (58 (48 err 55) (65 err 55)) (96 (95 err 55) (97 err (123 55 err))))
    (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err (123 26
    err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err (123
    26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (101 (= 96 err 26)
    (102 77 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (112
    (= 96 err 26) (113 78 (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (115 (= 96 err 26) (116 79 (123 26 err)))) (95 (58 (48 err
    26) (65 err (91 26 err))) (100 (= 96 err 26) (101 80 (123 26 err))))
    (95 (58 (48 err 26) (65 err (91 26 err))) (103 (= 96 err 26) (104 81
    (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (114 (= 96
    err 26) (115 82 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26
    err))) (116 (= 96 err 26) (117 83 (123 26 err)))) (95 (58 (48 err 26)
    (65 err (91 26 err))) (116 (= 96 err 26) (117 84 (123 26 err)))) (95
    (58 (48 err 26) (65 err (91 26 err))) (110 (= 96 err 26) (111 85 (123
    26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (110 (= 96 err 26)
    (111 86 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (108
    (= 96 err 26) (109 87 (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (100 (= 96 err 26) (101 88 (123 26 err)))) (95 (58 (48 err
    26) (65 err (91 26 err))) (109 (= 96 err 26) (110 89 (123 26 err))))
    err (45 (= 43 91 err) (48 (46 91 err) (58 90 err))) (48 err (58 73
    err)) (48 err (50 74 err)) (48 err (56 75 err)) (65 (48 err (58 76
    err)) (97 (71 76 err) (103 76 err))) (95 (58 (48 err 26) (65 err (91 26
    err))) (110 (= 96 err 26) (111 92 (123 26 err)))) (95 (58 (48 err 26)
    (65 err (91 26 err))) (101 (= 96 err 26) (102 93 (123 26 err)))) (95
    (58 (48 err 26) (65 err (91 26 err))) (101 (= 96 err 26) (102 94 (123
    26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err
    (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97
    err (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (117 (=
    96 err 26) (118 95 (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96
    (95 err 26) (97 err (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26
    err))) (117 (= 96 err 26) (118 96 (123 26 err)))) (95 (58 (48 err 26)
    (65 err (91 26 err))) (99 (= 96 err 26) (100 97 (123 26 err)))) (95 (58
    (48 err 26) (65 err (91 26 err))) (100 (= 96 err 26) (101 98 (123 26
    err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err (123
    26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (117 (= 96 err 26)
    (118 99 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (112
    (= 96 err 26) (113 100 (123 26 err)))) (48 err (58 90 err)) (48 err (58
    90 err)) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err (123
    26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err
    (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97
    err (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (99 (= 96
    err 26) (100 101 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26
    err))) (114 (= 96 err 26) (115 102 (123 26 err)))) (95 (58 (48 err 26)
    (65 err (91 26 err))) (116 (= 96 err 26) (117 103 (123 26 err)))) (95
    (58 (48 err 26) (65 err (91 26 err))) (105 (= 96 err 26) (106 104 (123
    26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (108 (= 96 err 26)
    (109 105 (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (111
    (= 96 err 26) (112 106 (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (116 (= 96 err 26) (117 107 (123 26 err)))) (95 (58 (48 err
    26) (65 err (91 26 err))) (110 (= 96 err 26) (111 108 (123 26 err))))
    (96 (65 (48 err (58 26 err)) (91 26 (95 err 26))) (106 (97 err (105 26
    110)) (112 (111 26 109) (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (110 (= 96 err 26) (111 111 (123 26 err)))) (95 (58 (48 err
    26) (65 err (91 26 err))) (101 (= 96 err 26) (102 112 (123 26 err))))
    (95 (58 (48 err 26) (65 err (91 26 err))) (110 (= 96 err 26) (111 113
    (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97
    err (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26)
    (97 err (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (114
    (= 96 err 26) (115 114 (123 26 err)))) (95 (58 (48 err 26) (65 err (91
    26 err))) (111 (= 96 err 26) (112 115 (123 26 err)))) (95 (58 (48 err
    26) (65 err (91 26 err))) (103 (= 96 err 26) (104 87 (123 26 err))))
    (91 (58 (48 err 26) (65 err 26)) (96 (95 err 26) (97 err (123 26
    err)))) (95 (58 (48 err 26) (65 err (91 26 err))) (101 (= 96 err 26)
    (102 116 (123 26 err)))) (91 (58 (48 err 26) (65 err 26)) (96 (95 err
    26) (97 err (123 26 err)))) (95 (58 (48 err 26) (65 err (91 26 err)))
    (110 (= 96 err 26) (111 117 (123 26 err)))) (95 (58 (48 err 26) (65 err
    (91 26 err))) (110 (= 96 err 26) (111 118 (123 26 err)))) (91 (58 (48
    err 26) (65 err 26)) (96 (95 err 26) (97 err (123 26 err)))) (95 (58
    (48 err 26) (65 err (91 26 err))) (116 (= 96 err 26) (117 112 (123 26
    err)))))
   '#((#f . #f) (52 . 52) (51 . 51) (50 . 50) (49 . 49) (46 . 46) (45 . 45)
    (42 . 42) (40 . 40) (39 . 39) (38 . 38) (37 . 37) (36 . 36) (35 . 35)
    (32 . 32) (30 . 30) (29 . 29) (#f . #f) (#f . #f) (25 . 25) (24 . 24)
    (23 . 23) (31 . 31) (41 . 41) (23 . 23) (#f . #f) (16 . 16) (16 . 16)
    (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16)
    (16 . 16) (16 . 16) (16 . 16) (48 . 48) (47 . 47) (44 . 44) (43 . 43)
    (34 . 34) (28 . 28) (27 . 27) (#f . #f) (22 . 22) (22 . 22) (33 . 33)
    (#f . #f) (#f . #f) (#f . #f) (#f . #f) (#f . #f) (#f . #f) (17 . 17)
    (13 . 13) (12 . 12) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16)
    (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16)
    (16 . 16) (26 . 26) (#f . #f) (21 . 21) (20 . 20) (19 . 19) (18 . 18)
    (16 . 16) (16 . 16) (16 . 16) (8 . 8) (11 . 11) (16 . 16) (6 . 6) (5 .
    5) (3 . 3) (16 . 16) (1 . 1) (16 . 16) (16 . 16) (22 . 22) (#f . #f)
    (14 . 14) (10 . 10) (15 . 15) (16 . 16) (16 . 16) (16 . 16) (16 . 16)
    (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16) (16 . 16)
    (16 . 16) (7 . 7) (4 . 4) (16 . 16) (16 . 16) (16 . 16) (0 . 0) (16 .
    16) (9 . 9) (16 . 16) (16 . 16) (2 . 2) (16 . 16))))

;
; User functions
;

(define lexer #f)

(define lexer-get-line   #f)
(define lexer-getc       #f)
(define lexer-ungetc     #f)

(define lexer-init
  (lambda (input-type input)
    (let ((IS (lexer-make-IS input-type input 'line)))
      (set! lexer (lexer-make-lexer lexer-default-table IS))
      (set! lexer-get-line   (lexer-get-func-line IS))
      (set! lexer-getc       (lexer-get-func-getc IS))
      (set! lexer-ungetc     (lexer-get-func-ungetc IS)))))
