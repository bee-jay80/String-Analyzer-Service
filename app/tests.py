from rest_framework.test import APITestCase
from django.urls import reverse
from .models import AnalyzedString
import hashlib


class StringAPITests(APITestCase):
	def test_create_and_get_string(self):
		url = reverse('create_string')
		payload = {'value': 'abc cba'}
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		data = resp.json()
		expected_hash = hashlib.sha256(payload['value'].encode('utf-8')).hexdigest()
		self.assertEqual(data['id'], expected_hash)

		# retrieve
		get_url = reverse('get_string_by_value', args=[payload['value']])
		g = self.client.get(get_url)
		self.assertEqual(g.status_code, 200)

	def test_conflict_on_duplicate(self):
		url = reverse('create_string')
		payload = {'value': 'dup'}
		r1 = self.client.post(url, payload, format='json')
		self.assertEqual(r1.status_code, 201)
		r2 = self.client.post(url, payload, format='json')
		self.assertEqual(r2.status_code, 409)

	def test_list_filters(self):
		# create a few
		self.client.post(reverse('create_string'), {'value': 'aba'}, format='json')
		self.client.post(reverse('create_string'), {'value': 'notpal'}, format='json')
		resp = self.client.get(reverse('list_strings') + '?is_palindrome=true')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertGreaterEqual(data['count'], 1)

	def test_nl_filter(self):
		self.client.post(reverse('create_string'), {'value': 'racecar'}, format='json')
		resp = self.client.get(reverse('filter_by_nl') + '?query=single%20word%20palindromic%20strings')
		self.assertEqual(resp.status_code, 200)
		j = resp.json()
		self.assertIn('interpreted_query', j)

	def test_delete(self):
		payload = {'value': 'todelete'}
		self.client.post(reverse('create_string'), payload, format='json')
		del_url = reverse('delete_by_value', args=[payload['value']])
		d = self.client.delete(del_url)
		self.assertEqual(d.status_code, 204)
