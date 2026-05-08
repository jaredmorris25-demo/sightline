import { useState, useEffect } from 'react'
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, Alert, ActivityIndicator, SafeAreaView
} from 'react-native'
import * as Location from 'expo-location'
import * as ImagePicker from 'expo-image-picker'
import { useRouter } from 'expo-router'
import { useAuth } from '../../lib/AuthContext'
import { apiClient } from '../../lib/api'

interface SpeciesSuggestion {
  id: string
  common_name: string | null
  scientific_name: string
}

export default function SubmitScreen() {
  const { isAuthenticated, accessToken } = useAuth()
  const router = useRouter()

  // Form state
  const [speciesQuery, setSpeciesQuery] = useState('')
  const [speciesSuggestions, setSpeciesSuggestions] = useState<SpeciesSuggestion[]>([])
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesSuggestion | null>(null)
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [observedAt, setObservedAt] = useState(new Date().toISOString().slice(0, 16))
  const [count, setCount] = useState('1')
  const [behaviourNotes, setBehaviourNotes] = useState('')
  const [visibility, setVisibility] = useState<'public' | 'private'>('public')
  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Get GPS on mount
  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync()
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({})
        setLatitude(loc.coords.latitude.toFixed(6))
        setLongitude(loc.coords.longitude.toFixed(6))
      }
    })()
  }, [])

  // Species typeahead — debounced 300ms
  useEffect(() => {
    if (speciesQuery.length < 2) {
      setSpeciesSuggestions([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await apiClient.get('/v1/search/species', { params: { q: speciesQuery } })
        setSpeciesSuggestions(res.data.items ?? res.data)
      } catch {
        setSpeciesSuggestions([])
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [speciesQuery])

  const pickPhoto = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    })
    if (!result.canceled) setPhoto(result.assets[0])
  }

  const handleSubmit = async () => {
    if (!selectedSpecies) { setError('Please select a species'); return }
    if (!latitude || !longitude) { setError('Location required'); return }

    setSubmitting(true)
    setError(null)

    try {
      // Create sighting
      const sightingRes = await apiClient.post('/v1/sightings/', {
        species_id: selectedSpecies.id,
        observed_at: new Date(observedAt).toISOString(),
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        count: parseInt(count) || 1,
        behaviour_notes: behaviourNotes || undefined,
        visibility,
      })
      const sighting = sightingRes.data

      // Upload photo if selected — non-blocking, sighting succeeds even if photo fails
      if (photo) {
        try {
          const presignRes = await apiClient.post('/v1/media/presign', {
            filename: photo.fileName ?? 'photo.jpg',
            content_type: photo.mimeType ?? 'image/jpeg',
            sighting_id: sighting.id,
          })
          const { media_id, upload_url } = presignRes.data

          const blob = await fetch(photo.uri).then(r => r.blob())
          await fetch(upload_url, {
            method: 'PUT',
            headers: {
              'Content-Type': photo.mimeType ?? 'image/jpeg',
              'x-ms-blob-type': 'BlockBlob',
            },
            body: blob,
          })

          await apiClient.post(`/v1/media/${media_id}/confirm`)
        } catch (photoErr) {
          console.error('Photo upload failed:', photoErr)
        }
      }

      router.replace('/(tabs)')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <View style={styles.centre}>
        <Text style={styles.loginPrompt}>Sign in to submit a sighting</Text>
      </View>
    )
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.heading}>Submit a sighting</Text>

        {/* Species search */}
        <Text style={styles.label}>Species *</Text>
        <TextInput
          style={styles.input}
          placeholder="Search species..."
          value={selectedSpecies ? (selectedSpecies.common_name ?? selectedSpecies.scientific_name) : speciesQuery}
          onChangeText={text => { setSelectedSpecies(null); setSpeciesQuery(text) }}
        />
        {speciesSuggestions.length > 0 && !selectedSpecies && (
          <View style={styles.suggestions}>
            {speciesSuggestions.slice(0, 5).map(s => (
              <TouchableOpacity
                key={s.id}
                style={styles.suggestion}
                onPress={() => { setSelectedSpecies(s); setSpeciesSuggestions([]) }}
              >
                <Text style={styles.suggestionText}>
                  {s.common_name ?? s.scientific_name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Location */}
        <Text style={styles.label}>Latitude *</Text>
        <TextInput style={styles.input} value={latitude} onChangeText={setLatitude} keyboardType="numeric" />
        <Text style={styles.label}>Longitude *</Text>
        <TextInput style={styles.input} value={longitude} onChangeText={setLongitude} keyboardType="numeric" />

        {/* Observed at */}
        <Text style={styles.label}>Observed at *</Text>
        <TextInput style={styles.input} value={observedAt} onChangeText={setObservedAt} />

        {/* Count */}
        <Text style={styles.label}>Count</Text>
        <TextInput style={styles.input} value={count} onChangeText={setCount} keyboardType="numeric" />

        {/* Behaviour notes */}
        <Text style={styles.label}>Behaviour notes</Text>
        <TextInput
          style={[styles.input, styles.multiline]}
          value={behaviourNotes}
          onChangeText={setBehaviourNotes}
          multiline
          numberOfLines={3}
        />

        {/* Visibility */}
        <Text style={styles.label}>Visibility</Text>
        <View style={styles.toggle}>
          {(['public', 'private'] as const).map(v => (
            <TouchableOpacity
              key={v}
              style={[styles.toggleBtn, visibility === v && styles.toggleActive]}
              onPress={() => setVisibility(v)}
            >
              <Text style={[styles.toggleText, visibility === v && styles.toggleTextActive]}>
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Photo */}
        <TouchableOpacity style={styles.photoBtn} onPress={pickPhoto}>
          <Text style={styles.photoBtnText}>
            {photo ? '📷 Photo selected' : '📷 Add photo (optional)'}
          </Text>
        </TouchableOpacity>

        {/* Error */}
        {error && <Text style={styles.error}>{error}</Text>}

        {/* Submit */}
        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.submitDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting
            ? <ActivityIndicator color="white" />
            : <Text style={styles.submitText}>Submit sighting</Text>
          }
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 16 },
  centre: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 20 },
  loginPrompt: { fontSize: 16, color: '#666', textAlign: 'center' },
  heading: { fontSize: 22, fontWeight: '700', marginBottom: 20, color: '#1a1a1a' },
  label: { fontSize: 14, fontWeight: '500', color: '#444', marginBottom: 4, marginTop: 12 },
  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 10, fontSize: 16 },
  multiline: { height: 80, textAlignVertical: 'top' },
  suggestions: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, marginTop: 2 },
  suggestion: { padding: 12, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  suggestionText: { fontSize: 15 },
  toggle: { flexDirection: 'row', gap: 8, marginTop: 4 },
  toggleBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', alignItems: 'center' },
  toggleActive: { backgroundColor: '#2d6a4f', borderColor: '#2d6a4f' },
  toggleText: { color: '#444', fontWeight: '500' },
  toggleTextActive: { color: 'white' },
  photoBtn: { marginTop: 16, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#2d6a4f', alignItems: 'center' },
  photoBtnText: { color: '#2d6a4f', fontWeight: '500' },
  error: { color: '#c0392b', marginTop: 12, textAlign: 'center' },
  submitBtn: { marginTop: 24, backgroundColor: '#2d6a4f', padding: 16, borderRadius: 12, alignItems: 'center' },
  submitDisabled: { opacity: 0.6 },
  submitText: { color: 'white', fontSize: 16, fontWeight: '600' },
})
