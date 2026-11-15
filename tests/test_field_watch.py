import unittest
from datetime import date, timedelta
from logic.crop_health import crop_health
from server import analiz_et


def weather(temp=12, rh=92, rain=2, days=7):
    start = date(2024, 5, 1)
    keys = [(start+timedelta(days=i)).strftime('%Y%m%d') for i in range(days)]
    return {'properties':{'parameter':{name:dict.fromkeys(keys, value) for name,value in [('T2M',temp),('RH2M',rh),('PRECTOTCORR',rain)]}}}


class FieldWatchTests(unittest.TestCase):
    def test_wheat_rust_favorable_historical(self):
        result = crop_health(weather(), 'buğday')
        rust = next(c for c in result['cards'] if c['id']=='rust')
        self.assertEqual((rust['status'],rust['matching_days']),('favorable',7))
        self.assertGreater(result['age_days'],7)

    def test_missing_humidity_does_not_invent_low_risk(self):
        raw=weather(); raw['properties']['parameter'].pop('RH2M')
        self.assertTrue(all(c['status']=='insufficient' for c in crop_health(raw)['cards']))

    def test_fill_values_and_nan_rejected(self):
        for bad in (-999, float('nan'), 101):
            self.assertEqual(crop_health(weather(rh=bad))['valid_days'],0)

    def test_no_overlap_rejected(self):
        raw=weather();raw['properties']['parameter']['RH2M']={'20230101':99}
        self.assertEqual(crop_health(raw)['valid_days'],0)

    def test_calendar_window_not_seven_scattered_days(self):
        raw=weather(); param=raw['properties']['parameter']
        for series in param.values(): series['20240615']=12
        result=crop_health(raw)
        self.assertEqual(result['valid_days'],1)
        self.assertTrue(all(c['status']=='insufficient' for c in result['cards']))

    def test_crop_specific_rules(self):
        self.assertNotIn('rust',[c['id'] for c in crop_health(weather(),'patates')['cards']])
        self.assertIn('blight',[c['id'] for c in crop_health(weather(),'patates')['cards']])

    def test_dry_weather_is_not_fungal_alert(self):
        cards=crop_health(weather(temp=22,rh=60,rain=0))['cards']
        self.assertEqual(cards[0]['status'],'low')
        self.assertEqual(cards[-1]['status'],'favorable')

    def test_minimum_samples(self):
        self.assertTrue(all(c['status']=='insufficient' for c in crop_health(weather(days=3))['cards']))

    def test_localization(self):
        self.assertIn('yellow rust', crop_health(weather(),'buğday','en')['cards'][1]['title'])

    def test_negative_temperatures_in_average(self):
        raw=weather(temp=-10);raw['properties']['parameter']['T2M']['bad']=-999
        self.assertEqual(analiz_et(raw)['sıcaklık_C'],-10)

if __name__=='__main__': unittest.main()
