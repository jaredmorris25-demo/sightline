import { useEffect, useState } from 'react'
import {
  StyleSheet, View, Text, FlatList, TextInput,
  TouchableOpacity, ActivityIndicator, SafeAreaView
} from 'react-native'
import { apiClient } from '../../lib/api'

interface Species {
  id: string
  common_name: string | null
  scientific_name: string
  kingdom: string | null
  family: string | null
  conservation_status: string | null
}

export default function SpeciesScreen() {
  const [species, setSpecies] = useState<Species[]>([])
  const [filtered, setFiltered] = useState<Species[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Species | null>(null)

  useEffect(() => {
<<<<<<< feature/us-002-species-browser
    apiClient.get('/v1/species/', { params: { limit: 255 } })
=======
    apiClient.get('/v1/species/', { params: { limit: 300 } })
>>>>>>> develop
      .then(res => {
        setSpecies(res.data.items)
        setFiltered(res.data.items)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!query.trim()) {
      setFiltered(species)
      return
    }
    const q = query.toLowerCase()
    setFiltered(species.filter(s =>
      s.common_name?.toLowerCase().includes(q) ||
      s.scientific_name.toLowerCase().includes(q)
    ))
  }, [query, species])

  if (loading) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator size="large" color="#2d6a4f" />
      </View>
    )
  }

  if (selected) {
    return (
      <SafeAreaView style={styles.container}>
        <TouchableOpacity onPress={() => setSelected(null)} style={styles.back}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <View style={styles.detail}>
          <Text style={styles.detailCommon}>
            {selected.common_name ?? selected.scientific_name}
          </Text>
          <Text style={styles.detailScientific}>{selected.scientific_name}</Text>
          {selected.kingdom && (
            <Text style={styles.detailMeta}>Kingdom: {selected.kingdom}</Text>
          )}
          {selected.family && (
            <Text style={styles.detailMeta}>Family: {selected.family}</Text>
          )}
          {selected.conservation_status && (
            <Text style={styles.detailMeta}>
              Conservation status: {selected.conservation_status}
            </Text>
          )}
        </View>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={styles.container}>
      <TextInput
        style={styles.search}
        placeholder="Search species..."
        value={query}
        onChangeText={setQuery}
        clearButtonMode="while-editing"
        autoCapitalize="none"
      />
      {filtered.length === 0 && (
        <Text style={styles.empty}>No species found for "{query}"</Text>
      )}
      <FlatList
        data={filtered}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.row}
            onPress={() => setSelected(item)}
          >
            <Text style={styles.commonName}>
              {item.common_name ?? item.scientific_name}
            </Text>
            <Text style={styles.scientificName}>{item.scientific_name}</Text>
          </TouchableOpacity>
        )}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  centre: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  search: {
    margin: 12,
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    fontSize: 16,
  },
  empty: { textAlign: 'center', color: '#999', marginTop: 40 },
  row: { paddingHorizontal: 16, paddingVertical: 12 },
  commonName: { fontSize: 16, fontWeight: '500', color: '#1a1a1a' },
  scientificName: { fontSize: 13, color: '#666', fontStyle: 'italic', marginTop: 2 },
  separator: { height: 1, backgroundColor: '#f0f0f0', marginLeft: 16 },
  back: { padding: 16 },
  backText: { color: '#2d6a4f', fontSize: 16, fontWeight: '600' },
  detail: { padding: 20 },
  detailCommon: { fontSize: 24, fontWeight: '700', color: '#1a1a1a' },
  detailScientific: { fontSize: 16, fontStyle: 'italic', color: '#666', marginTop: 4 },
  detailMeta: { fontSize: 15, color: '#444', marginTop: 12 },
})
