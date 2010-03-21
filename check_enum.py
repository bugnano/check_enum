#! /usr/bin/env python
# -*- coding: ascii -*-

# Copyright (c) 2007, Franco Bugnano
# All rights reserved.
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
#     1. The origin of this software must not be misrepresented; you must not
#     claim that you wrote the original software. If you use this software
#     in a product, an acknowledgment in the product documentation would be
#     appreciated but is not required.
#
#     2. Altered source versions must be plainly marked as such, and must not be
#     misrepresented as being the original software.
#
#     3. This notice may not be removed or altered from any source
#     distribution.

# Check automatico per gli array indicizzati da enum
# Estensioni al linguaggio C:
# All'interno di un commento
# // enum nome_enum INDEXES (Array1[], Array2[], Array3[]);
# Oppure
# /* enum nome_enum INDEXES (Array1[], Array2[], Array3[]); */
#
# Il ; e' opzionale
# enum e INDEXES sono case insensitive
#
# Ogni inizializzatore dell'array deve essere in uno di questi modi:
# /* VALORE_ENUM, */ ValoreArray,
# /* VALORE_ENUM, */ ValoreArray, // Eventuale commento
# /* VALORE_ENUM, */ ValoreArray, /* Eventuale commento */
# Il carattere di , sia nel valore enum che nell'inizializzatore e' opzionale
# Limitazione: Un solo inizializzatore per linea
#
# Questo programma non funziona se:
# - Si utilizzano direttive di preprocessore all'interno di enum o di inizializzazioni di array.
#   Esempio:
#   enum {
#   #ifdef PARTI_DA_0
#   VALORE0,
#   #endif
#   VALORE1
#	};
# - Gli inizializzatori dell'array sono delle stringhe ~ /[}][[:space:]]*;/
# - Ci sono delle stringhe contenenti //, /*, oppure */

# Copyright (C) 2007, Franco Bugnano

__version__ = '1.0.0'
__date__ = '2007-08-28'
__copyright__ = 'Copyright (C) 2007, Franco Bugnano'

import sys
import re

ReIndexes = re.compile(r'''
	/[/*]			# // oppure /*
	\s*				# Degli spazi opzionali
	enum\s+			# La parola enum seguita da 1 o piu' spazi
	(\w+)			# Il nome della enum
	\s+				# 1 o piu' spazi
	INDEXES\s*		# La parola INDEXES seguita da degli spazi opzionali
	[(]				# Parentesi aperta
	([^)]+)			# Tutto cio' cha sta prima della parentesi chiusa
	[)]\s*			# Parentesi chiusa seguita da degli spazi opzionali
	;?				# Carattere ; opzionale
	\s*				# Degli spazi opzionali
	([*]/.*)?		# Eventualmente */ e tutto il resto fino alla fine
	$				# Fine linea
''', re.DOTALL | re.IGNORECASE | re.VERBOSE)

ReQuadre = re.compile(r'''
	[[]		# Quadra aperta
	[^]]*	# Tutto cio' che non chiude la quadra
	[]]		# Quadra chiusa
''', re.DOTALL | re.VERBOSE)

ReEnum = re.compile(r'''
	\benum\b		# La parola enum
	\s*				# Degli spazi opzionali
	(\b\w+\b)?		# Eventuale nome della enum
	\s*				# Degli spazi opzionali
	[{]				# Graffa aperta
	([^}]+)			# Valori della enum
	[}]				# Graffa chiusa
	([^;]*)			# Eventuale nome della typedef
	;				# Carattere ;
''', re.DOTALL | re.VERBOSE)

ReArray = re.compile(r'''
	\b(?P<nome>\w+)\b			# Nome dell'array
	\s*							# Degli spazi opzionali
	[[]							# Quadra aperta
	[^]]*						# Tutto cio' che non chiude la quadra
	[]]							# Quadra chiusa
	[^=;]*						# Tutto cio' che non e' = o ;
	=							# Carattere =
	\s*							# Degli spazi opzionali
	[{]							# Graffa aperta
	(?P<valori>					# Inizio gruppo valori
		(?:						# Inizio gruppo ripetizione
			[^}]*				# Tutto cio ' che non e' }
			(?:					#
				(?![}]\s*;)		# A condizione che non sia una } seguita da spazi opzionali e ;
				[}]				# Carattere }
			)?					# Opzionale
		)*						# Fine gruppo ripetizione
	)							# Fine gruppo valori
	[}]\s*;						# Graffa chiusa, spazi opzionali e ;
''', re.DOTALL | re.VERBOSE)

ReInizializzatore = re.compile(r'''
	^			# Inizio stringa
	\s*			# Degli spazi opzionali
	/[*]		# /*
	\s*			# Degli spazi opzionali
	\b(\w+)\b	# Valore della enum
	\s*			# Degli spazi opzionali
	,?			# , opzionale
	\s*			# Degli spazi opzionali
	[*]/		# */
	.*			# Tutto il resto
	$			# Fine stringa
''', re.DOTALL | re.VERBOSE)

# Key: Nome enum
# Value: Lista elementi
TabElementiEnum = {}

# Key: Nome Array
# Value: Nome Enum associata
TabArrayEnum = {}

SetValoriEnum = set()

def ProcessaIndexes(linea):
	'''Cerca nela linea passata come parametro la direttiva INDEXES e compila le tabelle'''
	m = ReIndexes.search(linea)
	if m is None:
		return

	nome_enum = m.group(1)
	lista_array = m.group(2).split(',')
	lista_array = map(lambda x: ReQuadre.sub('', x).strip(), lista_array)
	lista_array = filter(lambda x: x != '', lista_array)
	if len(lista_array) != 0:
		for x in lista_array:
			TabArrayEnum[x] = nome_enum
		TabElementiEnum[nome_enum] = []


def TogliCommentiLinea(testo):
	senza_commenti = ''
	i_fine = 0
	while i_fine != -1:
		i_inizio = testo.find('//', i_fine)
		if i_inizio == -1:
			i_inizio = len(testo)
		senza_commenti += testo[i_fine:i_inizio]
		i_fine = testo.find('\n', i_inizio)

	return senza_commenti


def TogliCommentiBlocco(testo):
	senza_commenti = ''
	i_fine = 0
	while i_fine != 1:	# != 1 perche' sommo 2 all'indice trovato (-1 + 2 = 1)
		i_inizio = testo.find('/*', i_fine)
		if i_inizio == -1:
			i_inizio = len(testo)
		senza_commenti += testo[i_fine:i_inizio]
		i_fine = testo.find('*/', i_inizio) + 2

	return senza_commenti


def TogliCommentiTieniEnum(testo):
	lunghezza_testo = len(testo)
	senza_commenti = ''
	i_fine_prec = 0
	i_fine = 0
	while i_fine != lunghezza_testo:
		i_inizio = testo.find('/*', i_fine)
		if i_inizio == -1:
			i_inizio = lunghezza_testo

		i_fine = testo.find('*/', i_inizio) + 2
		if i_fine == 1:		# != 1 perche' sommo 2 all'indice trovato (-1 + 2 = 1)
			i_fine = lunghezza_testo

		commento = testo[i_inizio:i_fine]

		# Tolgo /* e */ ed eventuali spazi iniziali e finali
		commento = commento.replace('/*', '').replace('*/', '').strip()

		# Accetto anche il valore della enum con la , finale
		if (len(commento) > 0) and (commento[-1] == ','):
			commento = commento[:-1].strip()

		# Se il commento e' un valore di enum lo tengo, altrimenti lo scarto
		if commento in SetValoriEnum:
			senza_commenti += testo[i_fine_prec:i_fine]
		else:
			senza_commenti += testo[i_fine_prec:i_inizio]

		i_fine_prec = i_fine

	return senza_commenti


def CompilaValoriEnum(testo):
	i_fine = 0
	while True:
		m = ReEnum.search(testo, i_fine)
		if m is None:
			break

		i_fine = m.end()
		nome_enum = m.group(1)
		valori_enum = m.group(2).split(',')
		valori_enum = map(lambda x: x.strip(), valori_enum)
		valori_enum = filter(lambda x: x != '', valori_enum)
		nomi_typedef = m.group(3).split(',')
		nomi_typedef = map(lambda x: x.strip(), nomi_typedef)
		nomi_typedef = filter(lambda x: x != '', nomi_typedef)
		nomi_trovati = filter(lambda x: x in TabElementiEnum, nomi_typedef)
		if nome_enum in TabElementiEnum:
			nomi_trovati.append(nome_enum)
		for nome in nomi_trovati:
			if filter(lambda x: '=' in x, valori_enum):
				print '----------'
				print 'enum:     %s' % (nome)
				print 'Operazione di assegnazione non supportata'
				print '----------'
				sys.exit(1)
			TabElementiEnum[nome] = valori_enum
			SetValoriEnum.update(valori_enum)


def VerificaArray(testo):
	i_fine = 0
	while True:
		m = ReArray.search(testo, i_fine)
		if m is None:
			break

		i_fine = m.end()
		nome_array = m.group('nome')
		if nome_array in TabArrayEnum:
			valori_array = m.group('valori')
			VerificaInizializzatori(nome_array, valori_array)


def VerificaInizializzatori(nome_array, valori_array):
	i = 0
	linee = valori_array.split('\n')
	linee = map(lambda x: x.strip(), linee)
	linee = filter(lambda x: x != '', linee)
	nome_enum = TabArrayEnum[nome_array]
	valori_enum = TabElementiEnum[nome_enum]
	num_valori_enum = len(valori_enum)
	if len(linee) != num_valori_enum:
		print '----------'
		print 'Array:    %s' % (nome_array)
		print 'Numero di inizializzatori diverso dalla lunghezza della enum %s' % (nome_enum)
		print '----------'

	for linea in linee:
		if i >= num_valori_enum:
			print '----------'
			print 'Array:    %s' % (nome_array)
			print 'Troppi inizializzatori'
			print '----------'
			break

		m = ReInizializzatore.match(linea)
		if m is None:
			print '----------'
			print 'Array:    %s' % (nome_array)
			print 'Indice:   %u' % (i)
			print 'Corrispondenza non trovata'
			print 'Previsto: %s' % (valori_enum[i])
			print '----------'
			sys.exit(1)

		valore_trovato = m.group(1)
		if valore_trovato != valori_enum[i]:
			print '----------'
			print 'Array:    %s' % (nome_array)
			print 'Indice:   %u' % (i)
			print 'Trovato:  %s' % (valore_trovato)
			print 'Previsto: %s' % (valori_enum[i])
			print '----------'
			sys.exit(1)

		i += 1


def main(argv=None):
	if argv is None:
		argv = sys.argv

	lista_file = argv[1:]

	# TO DO -- Sarebbe da mettere anche la classica schermata Usage del tipo
	# Usage:
	# find . -iname '*.h' | xargs argv[0]

	# 1. Processo le direttive INDEXES
	for f in lista_file:
		fp = open(f, 'rU')
		for linea in fp:
			ProcessaIndexes(linea)
		fp.close()

	# 2. Processo le enum
	for f in lista_file:
		fp = open(f, 'rU')
		testo = fp.read()
		fp.close()
		CompilaValoriEnum(TogliCommentiBlocco(TogliCommentiLinea(testo)))

	# TO DO -- Sarebbe bello vedere se ho trovato tutte le enum elencate nelle INDEXES

	# 3. Verifico gli inizializzatori degli array
	for f in lista_file:
		fp = open(f, 'rU')
		testo = fp.read()
		fp.close()
		VerificaArray(TogliCommentiTieniEnum(TogliCommentiLinea(testo)))

	# TO DO -- Sarebbe bello vedere se ho verificato tutti gli array elencati nelle INDEXES


if __name__ == '__main__':
	sys.exit(main())

