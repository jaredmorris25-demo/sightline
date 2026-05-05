import { useEffect, useState } from 'react'
import { StyleSheet, View, Text, ActivityIndicator } from 'react-native'
import MapView, { Marker } from 'react-native-maps'
import * as Location from 'expo-location'
import { apiClient } from '../../lib/api'

interface Sighting {
  id: string
  latitude: number
  longitude: number
  species_common_name: string | null
  species_scientific_name: string | null
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
  const [selected, setSelected] = useState<Sighting | null>(null)

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync()
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({})
        setLocation(loc)
      }

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
            onPress={() => setSelected(s)}
          />
        ))}
      </MapView>
      {error && <Text style={styles.error}>{error}</Text>}
      {selected && (
        <View style={styles.panel}>
          <Text style={styles.panelTitle}>
            {selected.species_common_name ?? selected.species_scientific_name ?? 'Unknown species'}
          </Text>
          <Text style={styles.panelDate}>
            {new Date(selected.observed_at).toLocaleDateString('en-AU')}
          </Text>
          <Text style={styles.panelClose} onPress={() => setSelected(null)}>✕ Close</Text>
        </View>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  centre: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText: { marginTop: 12, color: '#555' },
  error: { position: 'absolute', bottom: 0, alignSelf: 'center', color: 'red' },
  panel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    padding: 20,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  panelTitle: { fontSize: 18, fontWeight: '600', color: '#1a1a1a' },
  panelDate: { color: '#666', marginTop: 4 },
  panelClose: { color: '#2d6a4f', marginTop: 12, fontWeight: '600' },
})
