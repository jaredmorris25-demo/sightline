import { useEffect, useState } from 'react'
import { StyleSheet, View, Text, ActivityIndicator, Platform } from 'react-native'
import MapView, { Marker, Callout } from 'react-native-maps'
import * as Location from 'expo-location'
import { apiClient } from '../../lib/api'

interface Sighting {
  id: string
  latitude: number
  longitude: number
  species_common_name: string
  observed_at: string
}

const AUSTRALIA_CENTRE = {
  latitude: -25.2744,
  longitude: 133.7751,
  latitudeDelta: 30,
  longitudeDelta: 30,
}

export default function MapScreen() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null)
  const [sightings, setSightings] = useState<Sighting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      // Request location permission
      const { status } = await Location.requestForegroundPermissionsAsync()
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({})
        setLocation(loc)
      }

      // Fetch sightings
      try {
        const res = await apiClient.get('/v1/sightings/map', { params: { limit: 500 } })
        setSightings(res.data.filter((s: Sighting) => s.latitude && s.longitude))
      } catch (e) {
        setError('Failed to load sightings')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator size="large" color="#2d6a4f" />
        <Text style={styles.loadingText}>Loading map...</Text>
      </View>
    )
  }

  const initialRegion = location
    ? {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 1,
        longitudeDelta: 1,
      }
    : AUSTRALIA_CENTRE

  return (
    <View style={styles.container}>
      <MapView style={styles.map} initialRegion={initialRegion} showsUserLocation>
        {sightings.map(s => (
          <Marker
            key={s.id}
            coordinate={{ latitude: s.latitude, longitude: s.longitude }}
            pinColor="#2d6a4f"
          >
            <Callout>
              <View style={styles.callout}>
                <Text style={styles.calloutTitle}>{s.species_common_name || 'Unknown species'}</Text>
                <Text style={styles.calloutDate}>
                  {new Date(s.observed_at).toLocaleDateString('en-AU')}
                </Text>
              </View>
            </Callout>
          </Marker>
        ))}
      </MapView>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  centre: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText: { marginTop: 12, color: '#555' },
  callout: { padding: 8, minWidth: 150 },
  calloutTitle: { fontWeight: '600', fontSize: 14 },
  calloutDate: { color: '#666', fontSize: 12, marginTop: 4 },
  error: { position: 'absolute', bottom: 20, alignSelf: 'center', color: 'red' },
})
