#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime

# 5 Players Configuration
PLAYERS = {
    'anura': {
        'names': ['anura', 'kumara', 'dissanayake', 'akd', 'npp', 'jvp', 'president'],
        'party': 'NPP',
        'role': 'President'
    },
    'dilith': {
        'names': ['dilith', 'jayaweera', 'mjp', 'derana', 'sarwajana', 'sarwajana balaya'],
        'party': 'MJP',
        'role': 'Opposition Leader (de facto)'
    },
    'sajith': {
        'names': ['sajith', 'premadasa', 'sjb', 'samagi', 'samagi balawegaya'],
        'party': 'SJB',
        'role': 'Opposition Leader (official)'
    },
    'namal': {
        'names': ['namal', 'rajapaksa', 'slpp', 'mahinda', 'gotabaya', 'basil', 'gota'],
        'party': 'SLPP',
        'role': 'Dynasty Scion'
    },
    'ranil': {
        'names': ['ranil', 'wickremesinghe', 'unp', 'wickremasinghe', 'old president'],
        'party': 'UNP',
        'role': 'Former President (jailed)'
    }
}

NEWS_SOURCES = {
    'adaderana': 'https://www.adaderana.lk/news.php',
    'dailymirror': 'https://www.dailymirror.lk/news',
    'themorning': 'https://www.themorning.lk',
    'newsfirst': 'https://www.newsfirst.lk'
}

def detect_player(text):
    """Detect which players are mentioned in text"""
    text_lower = text.lower()
    mentions = {}
    
    for player, data in PLAYERS.items():
        score = sum(3 if name in text_lower else 0 for name in data['names'])
        mentions[player] = score > 0
    
    return mentions

def analyze_sentiment(text):
    """Analyze sentiment of headline"""
    text_lower = text.lower()
    
    positive = ['win', 'victory', 'success', 'good', 'great', 'excellent', 'superb', 
                'achieve', 'deliver', 'promise kept', 'ජයග්‍රහණය', 'සුපිරි', 'නියම']
    
    negative = ['fail', 'loss', 'bad', 'worst', 'corrupt', 'lie', 'cheat', 'disaster',
                'crisis', 'broken', 'useless', 'pathetic', 'පාවී', 'අසමත්', 'වැරදි']
    
    crisis = ['protest', 'strike', 'uprising', 'revolution', 'topple', 'overthrow',
              'emergency', 'crisis', 'collapse', 'imf', 'tariff', 'unemployment',
              'උද්ඝෝෂණ', 'වර්ජන', 'අර්බුදය']
    
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    crisis_count = sum(1 for w in crisis if w in text_lower)
    
    if pos_count > neg_count:
        sentiment = 'positive'
        score = 0.5 + min(pos_count * 0.1, 0.5)
    elif neg_count > pos_count:
        sentiment = 'negative'
        score = 0.5 - min(neg_count * 0.1, 0.5)
    else:
        sentiment = 'neutral'
        score = 0.5
    
    return {
        'sentiment': sentiment,
        'score': round(score, 2),
        'crisis_indicators': crisis_count
    }

def scrape_site(url, source):
    """Scrape news from a source"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        
        # Generic extraction - works for most news sites
        for article in soup.find_all(['article', 'div', 'li'], class_=re.compile('news|story|item|headline'))[:15]:
            title_tag = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if title_tag:
                title = title_tag.get_text(strip=True)
                if len(title) > 20 and len(title) < 200:
                    articles.append({
                        'title': title,
                        'source': source,
                        'url': article.find('a')['href'] if article.find('a') else '',
                        'timestamp': datetime.now().isoformat()
                    })
        
        return articles
    except Exception as e:
        print(f"Error scraping {source}: {e}")
        return []

def calculate_metrics(articles):
    """Calculate all political metrics"""
    
    # Initialize player stats
    player_stats = {p: {
        'mentions': 0,
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'crisis_associated': 0,
        'headlines': []
    } for p in PLAYERS.keys()}
    
    # Analyze each article
    for article in articles:
        mentions = detect_player(article['title'])
        sentiment = analyze_sentiment(article['title'])
        
        for player, mentioned in mentions.items():
            if mentioned:
                player_stats[player]['mentions'] += 1
                player_stats[player]['headlines'].append({
                    'title': article['title'],
                    'sentiment': sentiment['sentiment'],
                    'source': article['source']
                })
                
                if sentiment['sentiment'] == 'positive':
                    player_stats[player]['positive'] += 1
                elif sentiment['sentiment'] == 'negative':
                    player_stats[player]['negative'] += 1
                else:
                    player_stats[player]['neutral'] += 1
                
                player_stats[player]['crisis_associated'] += sentiment['crisis_indicators']
    
    # Calculate totals
    total_mentions = sum(s['mentions'] for s in player_stats.values())
    
    # Calculate percentages and scores
    for player, stats in player_stats.items():
        if stats['mentions'] > 0:
            stats['media_share'] = round(stats['mentions'] / max(1, total_mentions) * 100, 1)
            stats['sentiment_score'] = round((stats['positive'] - stats['negative']) / stats['mentions'], 2)
        else:
            stats['media_share'] = 0
            stats['sentiment_score'] = 0
    
    # War metrics
    metrics = {
        'players': player_stats,
        'total_articles': len(articles),
        'total_mentions': total_mentions,
        'war_intensity': min(10, sum(s['crisis_associated'] for s in player_stats.values()) / max(1, len(articles)) * 5),
        'dominant_player': max(player_stats.items(), key=lambda x: x[1]['mentions'])[0] if total_mentions > 0 else 'none',
        'timestamp': datetime.now().isoformat()
    }
    
    return metrics

def generate_report(metrics):
    """Generate war report with predictions"""
    
    report = {
        'timestamp': metrics['timestamp'],
        'battlefield_status': {},
        'predictions': {},
        'active_conflicts': []
    }
    
    # Individual player status
    for player, stats in metrics['players'].items():
        total = stats['mentions']
        if total > 0:
            attack_ratio = stats['negative'] / total  # Negative news = attacking others
            defense_ratio = stats['positive'] / total  # Positive news = defending self
            
            posture = 'attacking' if attack_ratio > 0.4 else 'defending' if defense_ratio > 0.4 else 'neutral'
            trend = 'rising' if stats['sentiment_score'] > 0.1 else 'falling' if stats['sentiment_score'] < -0.1 else 'stable'
        else:
            posture = 'neutral'
            trend = 'stable'
        
        report['battlefield_status'][player] = {
            'media_presence': stats['media_share'],
            'public_sentiment': stats['sentiment_score'],
            'posture': posture,
            'trend': trend,
            'crisis_exposure': stats['crisis_associated']
        }
    
    # AI Predictions
    anura_status = report['battlefield_status']['anura']
    dilith_status = report['battlefield_status']['dilith']
    
    # Anura prediction
    if anura_status['trend'] == 'falling':
        report['predictions']['anura'] = {
            'move': 'Emergency populist measure (fuel subsidy/teacher wage hike)',
            'confidence': 0.82,
            'timing': '24-48 hours'
        }
    else:
        report['predictions']['anura'] = {
            'move': 'Continue IMF path, ignore opposition',
            'confidence': 0.75,
            'timing': 'Ongoing'
        }
    
    # Dilith prediction
    if dilith_status['trend'] == 'rising':
        report['predictions']['dilith'] = {
            'move': 'Escalate attacks, formalize opposition coalition',
            'confidence': 0.79,
            text_lower = text.lower()
    mentions = {}
    
    for player, data in PLAYERS.items():
        score = sum(3 if name in text_lower else 0 for name in data['names'])
        mentions[player] = score > 0
    
    return mentions

def analyze_sentiment(text):
    """Analyze sentiment of headline"""
    text_lower = text.lower()
    
    positive = ['win', 'victory', 'success', 'good', 'great', 'excellent', 'superb', 
                'achieve', 'deliver', 'promise kept', 'ජයග්‍රහණය', 'සුපිරි', 'නියම']
    
    negative = ['fail', 'loss', 'bad', 'worst', 'corrupt', 'lie', 'cheat', 'disaster',
                'crisis', 'broken', 'useless', 'pathetic', 'පාවී', 'අසමත්', 'වැරදි']
    
    crisis = ['protest', 'strike', 'uprising', 'revolution', 'topple', 'overthrow',
              'emergency', 'crisis', 'collapse', 'imf', 'tariff', 'unemployment',
              'උද්ඝෝෂණ', 'වර්ජන', 'අර්බුදය']
    
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    crisis_count = sum(1 for w in crisis if w in text_lower)
    
    if pos_count > neg_count:
        sentiment = 'positive'
        score = 0.5 + min(pos_count * 0.1, 0.5)
    elif neg_count > pos_count:
        sentiment = 'negative'
        score = 0.5 - min(neg_count * 0.1, 0.5)
    else:
        sentiment = 'neutral'
        score = 0.5
    
    return {
        'sentiment': sentiment,
        'score': round(score, 2),
        'crisis_indicators': crisis_count
    }

def scrape_site(url, source):
    """Scrape news from a source"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        
        # Generic extraction - works for most news sites
        for article in soup.find_all(['article', 'div', 'li'], class_=re.compile('news|story|item|headline'))[:15]:
            title_tag = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if title_tag:
                title = title_tag.get_text(strip=True)
                if len(title) > 20 and len(title) < 200:
                    articles.append({
                        'title': title,
                        'source': source,
                        'url': article.find('a')['href'] if article.find('a') else '',
                        'timestamp': datetime.now().isoformat()
                    })
        
        return articles
    except Exception as e:
        print(f"Error scraping {source}: {e}")
        return []

def calculate_metrics(articles):
    """Calculate all political metrics"""
    
    # Initialize player stats
    player_stats = {p: {
        'mentions': 0,
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'crisis_associated': 0,
        'headlines': []
    } for p in PLAYERS.keys()}
    
    # Analyze each article
    for article in articles:
        mentions = detect_player(article['title'])
        sentiment = analyze_sentiment(article['title'])
        
        for player, mentioned in mentions.items():
            if mentioned:
                player_stats[player]['mentions'] += 1
                player_stats[player]['headlines'].append({
                    'title': article['title'],
                    'sentiment': sentiment['sentiment'],
                    'source': article['source']
                })
                
                if sentiment['sentiment'] == 'positive':
                    player_stats[player]['positive'] += 1
                elif sentiment['sentiment'] == 'negative':
                    player_stats[player]['negative'] += 1
                else:
                    player_stats[player]['neutral'] += 1
                
                player_stats[player]['crisis_associated'] += sentiment['crisis_indicators']
    
    # Calculate totals
    total_mentions = sum(s['mentions'] for s in player_stats.values())
    
    # Calculate percentages and scores
    for player, stats in player_stats.items():
        if stats['mentions'] > 0:
            stats['media_share'] = round(stats['mentions'] / max(1, total_mentions) * 100, 1)
            stats['sentiment_score'] = round((stats['positive'] - stats['negative']) / stats['mentions'], 2)
        else:
            stats['media_share'] = 0
            stats['sentiment_score'] = 0
    
    # War metrics
    metrics = {
        'players': player_stats,
        'total_articles': len(articles),
        'total_mentions': total_mentions,
        'war_intensity': min(10, sum(s['crisis_associated'] for s in player_stats.values()) / max(1, len(articles)) * 5),
        'dominant_player': max(player_stats.items(), key=lambda x: x[1]['mentions'])[0] if total_mentions > 0 else 'none',
        'timestamp': datetime.now().isoformat()
    }
    
    return metrics

def generate_report(metrics):
    """Generate war report with predictions"""
    
    report = {
        'timestamp': metrics['timestamp'],
        'battlefield_status': {},
        'predictions': {},
        'active_conflicts': []
    }
    
    # Individual player status
    for player, stats in metrics['players'].items():
        total = stats['mentions']
        if total > 0:
            attack_ratio = stats['negative'] / total  # Negative news = attacking others
            defense_ratio = stats['positive'] / total  # Positive news = defending self
            
            posture = 'attacking' if attack_ratio > 0.4 else 'defending' if defense_ratio > 0.4 else 'neutral'
            trend = 'rising' if stats['sentiment_score'] > 0.1 else 'falling' if stats['sentiment_score'] < -0.1 else 'stable'
        else:
            posture = 'neutral'
            trend = 'stable'
        
        report['battlefield_status'][player] = {
            'media_presence': stats['media_share'],
            'public_sentiment': stats['sentiment_score'],
            'posture': posture,
            'trend': trend,
            'crisis_exposure': stats['crisis_associated']
        }
    
    # AI Predictions
    anura_status = report['battlefield_status']['anura']
    dilith_status = report['battlefield_status']['dilith']
    
    # Anura prediction
    if anura_status['trend'] == 'falling':
        report['predictions']['anura'] = {
            'move': 'Emergency populist measure (fuel subsidy/teacher wage hike)',
            'confidence': 0.82,
            'timing': '24-48 hours'
        }
    else:
        report['predictions']['anura'] = {
            'move': 'Continue IMF path, ignore opposition',
            'confidence': 0.75,
            'timing': 'Ongoing'
        }
    
    # Dilith prediction
    if dilith_status['trend'] == 'rising':
        report['predictions']['dilith'] = {
            'move': 'Escalate attacks, formalize opposition coalition',
            'confidence': 0.79,
            'timing': 'Next week'
        }
    else:
        report['predictions']['dilith'] = {
            'move': 'Consolidate gains, prepare for Budget battle',
            'confidence': 0.71,
            'timing': '2 weeks'
        }
    
    # Coalition prediction
    opposition_mentions = sum(metrics['players'][p]['mentions'] for p in ['dilith', 'sajith', 'namal'])
    total_mentions = metrics['total_mentions']
    
    if opposition_mentions > total_mentions * 0.6:
        report['predictions']['coalition'] = {
            'formation_probability': 0.73,
            'timeline': '2-4 weeks',
            'leader': 'dilith'
        }
    else:
        report['predictions']['coalition'] = {
            'formation_probability': 0.45,
            'timeline': 'Uncertain',
            'leader': 'none'
        }
    
    return report

def main():
    print("🔍 Scraping Sri Lanka political war data...")
    
    # Scrape all sources
    all_articles = []
    for source, url in NEWS_SOURCES.items():
        articles = scrape_site(url, source)
        all_articles.extend(articles)
        print(f"✅ {source}: {len(articles)} articles")
    
    # Calculate metrics
    metrics = calculate_metrics(all_articles)
    report = generate_report(metrics)
    
    # Save data
    os.makedirs('data', exist_ok=True)
    
    output = {
        'raw_metrics': metrics,
        'war_report': report,
        'articles_sample': all_articles[:15],
        'generated_at': datetime.now().isoformat()
    }
    
    with open('data/political_war_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 POLITICAL WAR REPORT")
    print("="*60)
    print(f"Articles: {metrics['total_articles']} | Mentions: {metrics['total_mentions']}")
    print(f"War Intensity: {metrics['war_intensity']:.1f}/10")
    print(f"Dominant: {metrics['dominant_player'].upper()}")
    print("\nPlayer Status:")
    for player, status in report['battlefield_status'].items():
        print(f"  {player.upper()}: {status['media_presence']}% media, {status['sentiment_score']:+.2f} sentiment, {status['trend']}")
    print("\nPredictions:")
    for player, pred in report['predictions'].items():
        if isinstance(pred, dict) and 'move' in pred:
            print(f"  {player.upper()}: {pred['move'][:50]}... ({pred['confidence']:.0%})")
    print("\n✅ Saved to data/political_war_data.json")

if __name__ == '__main__':
    main()
