from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AnalyzedString
from .serializers import AnalyzedStringSerializer
import hashlib
import re


def analyze_string(value: str) -> dict:
    """Compute properties of the string value."""
    if value is None:
        value = ''

    # Length (raw characters)
    length = len(value)

    # Word count: number of tokens separated by any whitespace
    words = re.findall(r'\S+', value)
    word_count = len(words)

    # Palindrome: case-insensitive exact match of the whole string (does not strip punctuation)
    is_palindrome = (value.lower() == value[::-1].lower())

    # Unique characters: distinct characters in the string (case-sensitive as characters differ)
    unique_characters = len(set(value))

    # SHA-256
    sha256_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()

    # Character frequency map: counts each character exactly as-is
    freq = {}
    for ch in value:
        freq[ch] = freq.get(ch, 0) + 1

    return {
        'length': length,
        'is_palindrome': is_palindrome,
        'unique_characters': unique_characters,
        'word_count': word_count,
        'sha256_hash': sha256_hash,
        'character_frequency_map': freq,
    }


@api_view(['POST'])
def create_string(request):
    """Create analyzed string. Request body: { "value": "..." }"""
    data = request.data
    if 'value' not in data:
        return Response({'detail': 'Missing "value" field'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(data['value'], str):
        return Response({'detail': 'Invalid data type for "value" (must be string)'},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    value = data['value']
    props = analyze_string(value)

    # If an object with same hash exists, return 409
    if AnalyzedString.objects.filter(id=props['sha256_hash']).exists():
        return Response({'detail': 'String already exists in the system'}, status=status.HTTP_409_CONFLICT)

    obj = AnalyzedString(
        value=value,
        length=props['length'],
        is_palindrome=props['is_palindrome'],
        unique_characters=props['unique_characters'],
        word_count=props['word_count'],
        character_frequency_map=props['character_frequency_map'],
    )
    # save() will set id and sha256_hash
    obj.save()

    serializer = AnalyzedStringSerializer(obj)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
def string_detail(request, string_value: str):
    """
    Handle GET and DELETE for /strings/{string_value}/
    GET -> retrieve by raw string value
    DELETE -> delete the analyzed string
    """
    hash_val = hashlib.sha256(string_value.encode('utf-8')).hexdigest()
    try:
        obj = AnalyzedString.objects.get(id=hash_val)
    except AnalyzedString.DoesNotExist:
        return Response({'detail': 'String does not exist in the system'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AnalyzedStringSerializer(obj)
        return Response(serializer.data)

    # DELETE
    obj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def list_strings(request):
    """List strings with optional filters as query params."""
    qs = AnalyzedString.objects.all()

    # Filters
    is_palindrome = request.query_params.get('is_palindrome')
    if is_palindrome is not None:
        if is_palindrome.lower() in ('true', '1'):
            qs = qs.filter(is_palindrome=True)
        elif is_palindrome.lower() in ('false', '0'):
            qs = qs.filter(is_palindrome=False)
        else:
            return Response({'detail': 'Invalid is_palindrome value'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        min_length = request.query_params.get('min_length')
        if min_length is not None:
            qs = qs.filter(length__gte=int(min_length))
        max_length = request.query_params.get('max_length')
        if max_length is not None:
            qs = qs.filter(length__lte=int(max_length))
        word_count = request.query_params.get('word_count')
        if word_count is not None:
            qs = qs.filter(word_count=int(word_count))
    except ValueError:
        return Response({'detail': 'Invalid numeric filter value'}, status=status.HTTP_400_BAD_REQUEST)

    contains_character = request.query_params.get('contains_character')
    if contains_character is not None:
        if len(contains_character) != 1:
            return Response({'detail': 'contains_character must be a single character'}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(value__contains=contains_character)

    # Build response
    serializer = AnalyzedStringSerializer(qs, many=True)
    data = serializer.data

    # Convert query params to a plain dict of applied filters (string values are fine)
    filters_applied = {k: v for k, v in request.query_params.items()}

    return Response({'data': data, 'count': len(data), 'filters_applied': filters_applied})

@api_view(['GET', 'POST'])
def handle_create_and_list(request):
    """Dispatch to create_string for POST and list_strings for GET."""
    method = request.method.upper()
    if method == 'POST':
        # If this view was already called with a DRF Request, unwrap it so
        # the decorated target view receives a plain django HttpRequest.
        raw_request = getattr(request, '_request', request)
        return create_string(raw_request)
    if method == 'GET':
        raw_request = getattr(request, '_request', request)
        return list_strings(raw_request)
    return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

def parse_nl_query(q: str):
    """
    Very small heuristic parser for a few example natural-language queries.
    Returns dict of parsed filters or raises ValueError for unparseable input.
    """
    if not q:
        raise ValueError('Empty query')

    q = q.lower()
    parsed = {}
    if 'single word' in q:
        parsed['word_count'] = 1
    if 'palindrom' in q:  # matches 'palindrome' or 'palindromic'
        parsed['is_palindrome'] = True

    # longer than N / longer than N characters
    m = re.search(r'longer than (\d+)', q)
    if m:
        # the user said "longer than 10" meaning min_length should be 11
        parsed['min_length'] = int(m.group(1)) + 1

    # containing the letter x
    m = re.search(r'containing the letter ([a-z])', q)
    if m:
        parsed['contains_character'] = m.group(1)

    # "first vowel" heuristic -> 'a'
    if 'first vowel' in q:
        parsed.setdefault('contains_character', 'a')

    if not parsed:
        raise ValueError('Unable to parse natural language query')

    return parsed


@api_view(['GET'])
def filter_by_nl(request):
    q = request.query_params.get('query')
    if q is None:
        return Response({'detail': 'Missing query parameter'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        parsed = parse_nl_query(q)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Validate parsed filters for contradictions (e.g., min_length > max_length)
    if 'min_length' in parsed and 'max_length' in parsed:
        if parsed['min_length'] > parsed['max_length']:
            return Response({'detail': 'Conflicting filters: min_length greater than max_length'},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if 'contains_character' in parsed and len(parsed['contains_character']) != 1:
        return Response({'detail': 'Parsed contains_character must be a single character'},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # Apply parsed filters
    qs = AnalyzedString.objects.all()
    if 'word_count' in parsed:
        qs = qs.filter(word_count=parsed['word_count'])
    if 'is_palindrome' in parsed:
        qs = qs.filter(is_palindrome=parsed['is_palindrome'])
    if 'min_length' in parsed:
        qs = qs.filter(length__gte=parsed['min_length'])
    if 'contains_character' in parsed:
        qs = qs.filter(value__contains=parsed['contains_character'])

    serializer = AnalyzedStringSerializer(qs, many=True)
    data = serializer.data

    return Response({
        'data': data,
        'count': len(data),
        'interpreted_query': {
            'original': q,
            'parsed_filters': parsed
        }
    })
